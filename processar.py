"""
Limpa, cruza e analisa os dados brutos de banda larga fixa (Anatel) x PIB (IBGE).

Uso: py processar.py
"""

import json
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).parent / "data" / "raw"
PROC_DIR = Path(__file__).parent / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)


def carregar_anatel() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "anatel_banda_larga_fixa_total_mensal.csv", sep=";", encoding="utf-8-sig")
    df.columns = ["ano", "mes", "acessos"]

    # Acessos é uma variável de estoque (acessos ativos no mês), não um fluxo.
    # Pra representar o trimestre uso o valor do último mês do trimestre
    # (mar/jun/set/dez), igual a como o próprio painel da Anatel reporta.
    df["trimestre"] = ((df["mes"] - 1) // 3) + 1
    fim_de_trimestre = df["mes"] % 3 == 0
    df = df[fim_de_trimestre].copy()

    df["periodo"] = df["ano"].astype(str) + "Q" + df["trimestre"].astype(str)
    df = df[["periodo", "ano", "trimestre", "acessos"]].sort_values("periodo").reset_index(drop=True)
    return df


def carregar_pib() -> pd.DataFrame:
    with open(RAW_DIR / "ibge_pib_trimestral_raw.json", encoding="utf-8") as f:
        registros = json.load(f)

    # A API SIDRA retorna o primeiro item como cabeçalho descritivo das colunas
    # (ex: {"D3C": "Trimestre (Código)", ...}), não como um dado de fato.
    df = pd.DataFrame(registros[1:])
    df = df.rename(columns={"V": "pib_milhoes_reais", "D3C": "codigo_periodo"})
    df["pib_milhoes_reais"] = pd.to_numeric(df["pib_milhoes_reais"], errors="coerce")

    codigo = df["codigo_periodo"].astype(str)
    df["ano"] = codigo.str[:4].astype(int)
    df["trimestre"] = codigo.str[4:].astype(int)
    df["periodo"] = df["ano"].astype(str) + "Q" + df["trimestre"].astype(str)

    df = df[["periodo", "ano", "trimestre", "pib_milhoes_reais"]].sort_values("periodo").reset_index(drop=True)
    return df


def carregar_pib_variacao_real() -> pd.DataFrame:
    """Taxa de crescimento real do PIB, dessazonalizada, trimestre contra
    trimestre anterior (tabela SIDRA 5932). Não tem efeito de inflação,
    diferente do pct_change sobre o valor nominal."""
    with open(RAW_DIR / "ibge_pib_variacao_real_raw.json", encoding="utf-8") as f:
        registros = json.load(f)

    df = pd.DataFrame(registros[1:])
    df = df.rename(columns={"V": "pib_var_pct_real", "D3C": "codigo_periodo"})
    df["pib_var_pct_real"] = pd.to_numeric(df["pib_var_pct_real"], errors="coerce")

    codigo = df["codigo_periodo"].astype(str)
    df["ano"] = codigo.str[:4].astype(int)
    df["trimestre"] = codigo.str[4:].astype(int)
    df["periodo"] = df["ano"].astype(str) + "Q" + df["trimestre"].astype(str)

    return df[["periodo", "pib_var_pct_real"]]


def cruzar_e_analisar(anatel: pd.DataFrame, pib: pd.DataFrame, pib_var_real: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(anatel, pib, on=["periodo", "ano", "trimestre"], how="inner")
    df = pd.merge(df, pib_var_real, on="periodo", how="left")
    df = df.sort_values("periodo").reset_index(drop=True)

    df["acessos_var_pct"] = df["acessos"].pct_change() * 100
    # variação nominal, mantida só de referência (mistura inflação com crescimento real)
    df["pib_var_pct_nominal"] = df["pib_milhoes_reais"].pct_change() * 100

    return df


def main():
    anatel = carregar_anatel()
    pib = carregar_pib()
    pib_var_real = carregar_pib_variacao_real()
    cruzado = cruzar_e_analisar(anatel, pib, pib_var_real)

    out_path = PROC_DIR / "dados_cruzados.csv"
    cruzado.to_csv(out_path, index=False)
    print(f"Dados cruzados salvos em: {out_path}")
    print(f"Período coberto: {cruzado['periodo'].iloc[0]} a {cruzado['periodo'].iloc[-1]} ({len(cruzado)} trimestres)")

    corr_niveis = cruzado["acessos"].corr(cruzado["pib_milhoes_reais"])
    corr_var_nominal = cruzado["acessos_var_pct"].corr(cruzado["pib_var_pct_nominal"])
    corr_var_real = cruzado["acessos_var_pct"].corr(cruzado["pib_var_pct_real"])

    print(f"\nCorrelação (níveis, acessos x PIB nominal): {corr_niveis:.3f}  [inflada pela tendência comum, pouco informativa]")
    print(f"Correlação (variação % trimestral, acessos x PIB nominal): {corr_var_nominal:.3f}")
    print(f"Correlação (variação % trimestral, acessos x PIB real dessazonalizado): {corr_var_real:.3f}  [métrica principal]")

    resumo = {
        "periodo_inicio": cruzado["periodo"].iloc[0],
        "periodo_fim": cruzado["periodo"].iloc[-1],
        "n_trimestres": len(cruzado),
        "correlacao_niveis": round(float(corr_niveis), 4),
        "correlacao_variacao_pct_nominal": round(float(corr_var_nominal), 4),
        "correlacao_variacao_pct_real": round(float(corr_var_real), 4),
    }
    with open(PROC_DIR / "resumo.json", "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
