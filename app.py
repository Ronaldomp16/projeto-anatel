"""
Relatório: Banda Larga Fixa (Anatel) x PIB (IBGE), Brasil, 2007T1-2026T1

Uso: py -m streamlit run app.py
"""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "processed" / "dados_cruzados.csv"

COR_ACESSOS = "#2a78d6"  # blue, slot 1
COR_PIB = "#1baf7a"      # aqua, slot 2
COR_MUTED = "#898781"
COR_GRID = "#e1e0d9"

st.set_page_config(page_title="Banda Larga x PIB", layout="centered")


@st.cache_data
def carregar_dados():
    df = pd.read_csv(DATA_PATH)
    df["periodo_dt"] = pd.PeriodIndex(df["ano"].astype(str) + "Q" + df["trimestre"].astype(str), freq="Q").to_timestamp()

    # índice de base 100 no primeiro trimestre, pra comparar as duas séries
    # numa escala comum, sem recorrer a eixo duplo.
    df["acessos_indice"] = df["acessos"] / df["acessos"].iloc[0] * 100
    df["pib_indice"] = df["pib_milhoes_reais"] / df["pib_milhoes_reais"].iloc[0] * 100

    return df


df = carregar_dados()

st.title("Banda larga fixa x PIB")
st.caption("Brasil, séries trimestrais, 2007T1 a 2026T1")

st.markdown(
    """
Este relatório cruza a série de **acessos de banda larga fixa** (Anatel, dados
abertos) com o **PIB trimestral** (IBGE/SIDRA) pra ver se a expansão da
infraestrutura de telecom acompanha o ciclo econômico ou segue um ritmo
próprio. Os acessos são o valor de fim de cada trimestre; o PIB é reportado
tanto em valores correntes quanto em taxa real de crescimento dessazonalizada.
"""
)

# ---------------------------------------------------------------------------
# Gráfico 1: evolução das duas séries, indexada a 100 no primeiro trimestre
# ---------------------------------------------------------------------------
st.subheader("Evolução (índice, 1º trimestre de 2007 = 100)")

base = df[["periodo_dt", "acessos_indice", "pib_indice"]].melt(
    id_vars="periodo_dt", var_name="serie", value_name="indice"
)
base["serie"] = base["serie"].map(
    {"acessos_indice": "Acessos banda larga fixa", "pib_indice": "PIB (valores correntes)"}
)

cor_scale = alt.Scale(
    domain=["Acessos banda larga fixa", "PIB (valores correntes)"],
    range=[COR_ACESSOS, COR_PIB],
)

linhas = (
    alt.Chart(base)
    .mark_line(strokeWidth=2)
    .encode(
        x=alt.X("periodo_dt:T", title=None, axis=alt.Axis(gridColor=COR_GRID, tickColor=COR_MUTED)),
        y=alt.Y("indice:Q", title="Índice (base 100)", axis=alt.Axis(gridColor=COR_GRID, tickColor=COR_MUTED)),
        color=alt.Color("serie:N", scale=cor_scale, legend=alt.Legend(title=None, orient="top")),
        tooltip=[
            alt.Tooltip("periodo_dt:T", title="Trimestre", format="%Y-%m"),
            alt.Tooltip("serie:N", title="Série"),
            alt.Tooltip("indice:Q", title="Índice", format=".1f"),
        ],
    )
)

rotulos = (
    alt.Chart(base[base["periodo_dt"] == base["periodo_dt"].max()])
    .mark_text(align="left", dx=6, fontWeight="bold")
    .encode(
        x="periodo_dt:T",
        y="indice:Q",
        text="serie:N",
        color=alt.Color("serie:N", scale=cor_scale, legend=None),
    )
)

st.altair_chart((linhas + rotulos).properties(height=380).interactive(bind_y=False), use_container_width=True)

st.caption(
    f"Acessos cresceram {df['acessos_indice'].iloc[-1] - 100:.0f}% e o PIB nominal "
    f"{df['pib_indice'].iloc[-1] - 100:.0f}% no período. O PIB nominal inclui inflação acumulada."
)

# ---------------------------------------------------------------------------
# Gráfico 2: dispersão das variações trimestrais (crescimento x crescimento)
# ---------------------------------------------------------------------------
st.subheader("Correlação: crescimento trimestral de acessos x crescimento real do PIB")

disp = df.dropna(subset=["acessos_var_pct", "pib_var_pct_real"])
corr = disp["acessos_var_pct"].corr(disp["pib_var_pct_real"])

pontos = (
    alt.Chart(disp)
    .mark_circle(size=70, color=COR_ACESSOS, opacity=0.75)
    .encode(
        x=alt.X("pib_var_pct_real:Q", title="Variação real do PIB no trimestre (%)", axis=alt.Axis(gridColor=COR_GRID)),
        y=alt.Y("acessos_var_pct:Q", title="Variação de acessos no trimestre (%)", axis=alt.Axis(gridColor=COR_GRID)),
        tooltip=[
            alt.Tooltip("periodo:N", title="Trimestre"),
            alt.Tooltip("pib_var_pct_real:Q", title="Var. PIB real (%)", format=".2f"),
            alt.Tooltip("acessos_var_pct:Q", title="Var. acessos (%)", format=".2f"),
        ],
    )
)

tendencia = pontos.transform_regression("pib_var_pct_real", "acessos_var_pct").mark_line(
    color=COR_MUTED, strokeDash=[4, 4], strokeWidth=1.5
)

st.altair_chart((pontos + tendencia).properties(height=380), use_container_width=True)
st.caption(f"Correlação (Pearson) entre as duas variações trimestrais: **r = {corr:.2f}**")

# ---------------------------------------------------------------------------
# Conclusão
# ---------------------------------------------------------------------------
st.subheader("Conclusão")
st.markdown(
    f"""
Em nível, as duas séries parecem quase perfeitamente correlacionadas
(r = {df['acessos'].corr(df['pib_milhoes_reais']):.2f}), mas isso é enganoso: ambas
só crescem ao longo do tempo, então qualquer duas séries assim tendem a
parecer correlacionadas. O teste mais honesto é comparar as **variações
trimestre a trimestre**, e aí a correlação cai pra **r = {corr:.2f}**, fraca.
Os dados sugerem que a expansão da banda larga fixa no Brasil segue uma
tendência estrutural própria (adoção de infraestrutura, migração de
tecnologias, concorrência entre prestadoras) mais do que um reflexo direto do
ciclo econômico de curto prazo: mesmo em trimestres de retração do PIB (como
2015-2016 e o início de 2020), os acessos praticamente não recuaram.
"""
)

with st.expander("Ver dados usados nesta análise"):
    st.dataframe(
        df[["periodo", "acessos", "pib_milhoes_reais", "acessos_var_pct", "pib_var_pct_real"]],
        use_container_width=True,
    )

st.caption("Fontes: Anatel (Painel de Dados Abertos) e IBGE/SIDRA (tabelas 1846 e 5932).")
