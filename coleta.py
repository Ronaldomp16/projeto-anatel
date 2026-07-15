"""
Coleta os dados brutos usados na análise:
  - Anatel: acessos totais de banda larga fixa (mensal), extraído do pacote
    oficial de dados abertos (arquivo agregado, sem o detalhe por prestadora/UF).
  - IBGE/SIDRA: PIB trimestral a preços de mercado, valores correntes (tabela 1846).

Uso: py coleta.py
"""

import io
import zipfile
from pathlib import Path

import requests

RAW_DIR = Path(__file__).parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

ANATEL_ZIP_URL = "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/acessos/acessos_banda_larga_fixa.zip"
ANATEL_MEMBER = "Acessos_Banda_Larga_Fixa_Total.csv"
ANATEL_OUT = RAW_DIR / "anatel_banda_larga_fixa_total_mensal.csv"

SIDRA_URL = "https://apisidra.ibge.gov.br/values/t/1846/n1/1/v/585/p/all/c11255/90707"
SIDRA_OUT = RAW_DIR / "ibge_pib_trimestral_raw.json"

# Tabela 5932: taxa de variação real do PIB (série dessazonalizada), var. 6564 =
# "trimestre contra trimestre imediatamente anterior". Usada na análise de
# correlação em vez do valor nominal, pra não misturar efeito de inflação.
SIDRA_VAR_URL = "https://apisidra.ibge.gov.br/values/t/5932/n1/1/v/6564/p/all/c11255/90707"
SIDRA_VAR_OUT = RAW_DIR / "ibge_pib_variacao_real_raw.json"


def baixar_anatel():
    """O ZIP completo tem ~1GB (dados por prestadora/UF/mês). Baixo só o
    membro agregado nacional, que já vem pronto pro caso de uso daqui."""
    print("Baixando pacote de acessos da Anatel (pode levar um tempo, ~1GB)...")
    resp = requests.get(ANATEL_ZIP_URL, timeout=180)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        with z.open(ANATEL_MEMBER) as f:
            ANATEL_OUT.write_bytes(f.read())
    print(f"OK: {ANATEL_OUT}")


def baixar_pib():
    print("Baixando série de PIB trimestral, valores correntes (SIDRA/IBGE)...")
    resp = requests.get(SIDRA_URL, timeout=60)
    resp.raise_for_status()
    SIDRA_OUT.write_bytes(resp.content)
    print(f"OK: {SIDRA_OUT}")

    print("Baixando taxa de variação real do PIB, dessazonalizada (SIDRA/IBGE)...")
    resp = requests.get(SIDRA_VAR_URL, timeout=60)
    resp.raise_for_status()
    SIDRA_VAR_OUT.write_bytes(resp.content)
    print(f"OK: {SIDRA_VAR_OUT}")


if __name__ == "__main__":
    baixar_pib()
    baixar_anatel()
