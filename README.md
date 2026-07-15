# Banda larga fixa x PIB

Mini análise cruzando a série de acessos de banda larga fixa (Anatel) com o
PIB trimestral do Brasil (IBGE), pra ver se a expansão da infraestrutura de
telecom acompanha o ciclo econômico ou segue um ritmo próprio.

**Período:** 2007T1 a 2026T1 (77 trimestres)

## Fontes de dados

- **Anatel**: [Painel de Dados Abertos](https://www.gov.br/anatel/pt-br/dados/dados-abertos), total de acessos de banda larga fixa (SCM), série mensal agregada nacionalmente.
- **IBGE/SIDRA**: [Contas Nacionais Trimestrais](https://sidra.ibge.gov.br/tabela/1846), PIB a preços de mercado (valores correntes) e [taxa de variação real dessazonalizada](https://sidra.ibge.gov.br/tabela/5932), trimestre contra trimestre anterior.

## Como rodar

```bash
pip install -r requirements.txt

# (opcional, os dados brutos já estão versionados em data/raw)
python coleta.py

python processar.py           # gera data/processed/dados_cruzados.csv
streamlit run app.py          # abre o relatório interativo
```

## Estrutura

```
coleta.py      # baixa os dados brutos (Anatel + IBGE/SIDRA)
processar.py   # limpa, cruza os dois datasets por trimestre e calcula correlações
app.py         # relatório interativo (Streamlit): gráficos + conclusão
data/raw/      # dados originais, como baixados das fontes
data/processed/  # dataset cruzado (dados_cruzados.csv) e resumo (resumo.json)
```

## Principal achado

Em nível, as duas séries parecem quase perfeitamente correlacionadas
(r = 0,995), mas isso é enganoso, já que ambas só crescem ao longo do tempo.
Comparando as **variações trimestre a trimestre**, a correlação cai para
r ≈ 0,16-0,19 (fraca). Os dados sugerem que a expansão da banda larga fixa no
Brasil segue uma tendência estrutural própria (adoção de infraestrutura,
migração tecnológica, concorrência entre prestadoras), mais do que um reflexo
direto do ciclo econômico de curto prazo. Os acessos praticamente não
recuaram mesmo em trimestres de retração do PIB, como 2015-2016 e o início de
2020.
