"""Dashboard — Garimpo Alpha B3.

Storytelling do macro ao específico, em quadros: visão geral → ranking →
detalhe da ação → risco de carteira. Base clara, cor com função.

Rodar:  uv run streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from src.db import get_engine  # noqa: E402
from src.fundamental.lynch import crescimento_lucro  # noqa: E402
from src.montecarlo.portfolio import retornos_mensais, simular_retornos_carteira  # noqa: E402
from src.montecarlo.valuation import simular_valores  # noqa: E402

st.set_page_config(page_title="Garimpo Alpha B3", page_icon="📊", layout="wide")

INDIGO, VERDE, AMBAR, VERMELHO = "#4F46E5", "#16A34A", "#D97706", "#DC2626"
TINTA, CINZA, GRID = "#0F172A", "#64748B", "#E2E8F0"
CORES_CLASSE = {"Buy": VERDE, "Hold": AMBAR, "Avoid": VERMELHO, "N/A": CINZA}


def estilo(fig: go.Figure, altura: int = 280) -> go.Figure:
    fig.update_layout(
        height=altura, margin=dict(l=10, r=10, t=48, b=30), bargap=0.08,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TINTA, size=13), showlegend=False,
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor="#CBD5E1")
    fig.update_yaxes(gridcolor=GRID, zerolinecolor="#CBD5E1")
    return fig


@st.cache_data(ttl=300)
def carregar():
    e = get_engine()
    gold = pd.read_sql("select * from gold_fundamental_scores order by ranking", e)
    silver = pd.read_sql("select * from silver_fundamentals", e)
    precos = pd.read_sql("select ticker, data, close from bronze_prices", e)
    precos["data"] = pd.to_datetime(precos["data"])
    meta = pd.read_sql("select * from meta_pipeline", e).iloc[0]
    return gold, silver, precos, meta


try:
    gold, silver, precos, meta = carregar()
except Exception as exc:
    st.error(f"Não consegui ler os dados: {exc}")
    st.stop()


def selos_txt(row: pd.Series) -> str:
    s = []
    if row.get("selo_fundamentos"):
        s.append("✅")
    if row.get("selo_subvalorizada"):
        s.append("💎")
    if row.get("selo_risco_baixo"):
        s.append("🛡️")
    return " ".join(s)


gold["selos"] = gold.apply(selos_txt, axis=1)

# ====================== cabecalho ======================
atualizado = pd.to_datetime(meta["atualizado_em"])
ch1, ch2 = st.columns([3, 1], vertical_alignment="center")
with ch1:
    st.title("Garimpo Alpha B3")
with ch2:
    st.markdown(
        f"<div style='text-align:right;color:{CINZA};font-size:0.9rem'>Atualizado em<br>"
        f"<b style='color:{TINTA};font-size:1.05rem'>{atualizado:%d/%m/%Y %H:%M}</b></div>",
        unsafe_allow_html=True,
    )
st.markdown(
    f"<span style='color:{CINZA}'>Ranqueamento de ações da B3 por fundamentos, com "
    "valuation e risco probabilísticos. Projeto educacional — não é recomendação.</span>",
    unsafe_allow_html=True,
)
st.write("")

# ====================== KPIs (cada um num quadro) ======================
kpis = st.columns(4)
topo = gold.iloc[0]
dados_kpi = [
    ("Ações analisadas", f"{int(meta['n_acoes'])}", None),
    ("Oportunidades (Buy)", f"{int((gold['classificacao'] == 'Buy').sum())}", None),
    ("Subvalorizadas 💎", f"{int(gold['selo_subvalorizada'].sum())}", None),
    ("1º do ranking", topo["ticker"], None),
]
for col, (label, valor, delta) in zip(kpis, dados_kpi):
    with col.container(border=True):
        st.metric(label, valor, delta)

# ====================== ranking (quadro) ======================
with st.container(border=True):
    st.subheader("Ranking de ações")
    st.caption(
        "Cada ação recebe um **score** que combina 5 métodos fundamentalistas (Graham, "
        "Buffett, EV/EBITDA, Lynch e DCF), padronizados e comparados entre si. Quanto maior "
        "o score, melhor. **Selos:** ✅ fundamentos fortes · 💎 preço abaixo do valor justo · "
        "🛡️ risco (volatilidade) abaixo da mediana."
    )
    vis = gold[
        ["ranking", "ticker", "setor", "selos", "score_final",
         "z_graham", "z_buffett", "z_evebitda", "z_lynch", "z_dcf", "classificacao"]
    ].rename(columns={
        "z_graham": "Graham", "z_buffett": "Buffett", "z_evebitda": "EV/EBITDA",
        "z_lynch": "Lynch", "z_dcf": "DCF", "score_final": "score", "classificacao": "sinal",
    })

    def cor_classe(v):
        return f"color:{CORES_CLASSE.get(v, CINZA)};font-weight:700"

    def cor_score(v):
        return f"color:{VERDE if v >= 0 else VERMELHO};font-weight:700" if pd.notna(v) else ""

    cols_z = ["score", "Graham", "Buffett", "EV/EBITDA", "Lynch", "DCF"]
    styled = vis.style.map(cor_classe, subset=["sinal"]).map(cor_score, subset=["score"]).format(
        {c: "{:+.2f}" for c in cols_z}, na_rep="—"
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=380)

# ====================== detalhe da acao (quadro) ======================
with st.container(border=True):
    st.subheader("Detalhe da ação")
    tk = st.selectbox("Ação", gold["ticker"].tolist(), index=0, label_visibility="collapsed")
    linha = gold[gold["ticker"] == tk].iloc[0]
    sil = silver[silver["ticker"] == tk].sort_values("ano")
    ult = sil.iloc[-1]
    st.markdown(
        f"**{tk}** · {linha['setor']} · "
        f"<span style='color:{CORES_CLASSE.get(linha['classificacao'], CINZA)};font-weight:700'>"
        f"{linha['classificacao']}</span> &nbsp; {selos_txt(linha)}",
        unsafe_allow_html=True,
    )

    # pre-computa o valuation para alinhar as colunas (ambas terminam no grafico)
    eh_op = ult["setor"] == "operacional" and pd.notna(ult["fco_mil"])
    valores = preco = prob = None
    if eh_op:
        cresc = crescimento_lucro(sil["fco_mil"].tolist(), sil["ano"].tolist())
        valores = simular_valores(
            ult["fco_mil"], cresc, float(meta["selic"]),
            ult["divida_liquida_mil"], ult["acoes_circulacao_mil"],
        )
        preco = linha["preco_atual"]
        if valores.size and pd.notna(preco):
            prob = float((valores > preco).mean())

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.markdown("**Pontos fortes e fracos por método**")
        st.caption("Cada barra: desvios-padrão acima (verde) ou abaixo (vermelho) da média do universo.")
        metodos = ["Graham", "Buffett", "EV/EBITDA", "Lynch", "DCF"]
        zs = [linha["z_graham"], linha["z_buffett"], linha["z_evebitda"],
              linha["z_lynch"], linha["z_dcf"]]
        fig = go.Figure(go.Bar(
            x=zs, y=metodos, orientation="h",
            marker_color=[VERDE if (pd.notna(v) and v >= 0) else VERMELHO for v in zs],
        ))
        fig.update_layout(xaxis_title="z-score (vs. média do universo)")
        st.plotly_chart(estilo(fig, 300), use_container_width=True)

    with col_b:
        st.markdown(f"**Quanto {tk} vale? — valor justo em R$ (Monte Carlo)**")
        if prob is not None:
            st.caption("2.500 cenários do valor justo; a linha vermelha é o preço de hoje.")
            fig2 = go.Figure(go.Histogram(x=valores, nbinsx=40, marker_color=INDIGO, opacity=0.8))
            fig2.add_vline(x=preco, line_color=VERMELHO, line_width=3,
                           annotation_text=f"preço R$ {preco:.0f}", annotation_position="top")
            fig2.update_layout(xaxis_title="valor justo por ação (R$)", yaxis_title="nº de cenários")
            st.plotly_chart(estilo(fig2, 300), use_container_width=True)
        else:
            st.caption("Valuation por fluxo de caixa só se aplica a empresas operacionais.")
            st.info("Bancos e holdings usam outra lógica de valuation.")

    if prob is not None:
        st.markdown(
            f"➡️ **{prob:.0%}** dos cenários dão valor acima do preço — "
            f"**{prob:.0%} de chance de {tk} estar subvalorizada**."
        )

# ====================== risco da carteira (quadro) ======================
with st.container(border=True):
    st.subheader("E se eu investir nas 3 melhores? (risco em 6 meses)")
    topn = gold.head(3)["ticker"].tolist()
    st.caption(
        f"As 3 são **sempre as primeiras do ranking atual** ({', '.join(topn)}) — **mudam** "
        "quando o pipeline é reexecutado com dados novos. Outra simulação de Monte Carlo, mas "
        "aqui o eixo é o **retorno em %** de uma **carteira** (não o valor de uma ação em R$). "
        "Rodamos 2.500 cenários de 6 meses para uma carteira dividida igualmente entre as 3."
    )
    finais, _ = simular_retornos_carteira(retornos_mensais(precos, topn), horizonte=6)
    mediana = float(pd.Series(finais).median())
    p95 = float(pd.Series(finais).quantile(0.95))
    var5 = float(pd.Series(finais).quantile(0.05))
    cvar5 = float(finais[finais <= var5].mean())

    r1, r2, r3 = st.columns(3)
    r1.metric("Cenário típico (mediana)", f"{mediana:+.1%}")
    r2.metric("Cenário otimista (5% melhores)", f"{p95:+.1%}")
    r3.metric("Cenário pessimista (5% piores)", f"{var5:+.1%}",
              help=f"VaR: perda superada só em 5% dos casos. Na média desses, CVaR = {cvar5:+.1%}.")

    fig3 = go.Figure(go.Histogram(x=finais * 100, nbinsx=50, marker_color=INDIGO, opacity=0.8))
    fig3.add_vline(x=0, line_color=CINZA, line_dash="dot")
    fig3.add_vline(x=mediana * 100, line_color=VERDE, line_width=3,
                   annotation_text="típico", annotation_position="top")
    fig3.add_vline(x=var5 * 100, line_color=VERMELHO, line_width=3,
                   annotation_text="pior 5%", annotation_position="top")
    fig3.update_layout(xaxis_title="retorno da carteira em 6 meses (%)", yaxis_title="nº de cenários")
    st.plotly_chart(estilo(fig3, 300), use_container_width=True)

    prob_ganho = float((finais > 0).mean())
    st.markdown(
        f"**Leitura:** em **{prob_ganho:.0%}** dos cenários a carteira termina no positivo; "
        f"no típico rende **{mediana:+.1%}** em 6 meses, mas num cenário ruim (5% piores) a "
        f"perda chega a **{var5:.1%}** ou mais."
    )
