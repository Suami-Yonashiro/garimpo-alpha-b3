"""Dashboard — Garimpo Alpha B3 (3 pilares: fundamental, ML/backtest, Monte Carlo).

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
from src.montecarlo.portfolio import retornos_mensais, simular_carteira  # noqa: E402
from src.montecarlo.valuation import simular_valores  # noqa: E402

st.set_page_config(page_title="Garimpo Alpha B3", page_icon="📊", layout="wide")
VERDE, AMBAR, VERMELHO = "#16C784", "#d97706", "#dc2626"
CORES = {"Buy": VERDE, "Hold": AMBAR, "Avoid": VERMELHO, "N/A": "#6b7280"}


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

# ---------- cabecalho + ultima atualizacao ----------
st.title("📊 Garimpo Alpha B3")
atualizado = pd.to_datetime(meta["atualizado_em"])
precos_ate = pd.to_datetime(meta["precos_ate"])
st.caption(
    f"Ranking fundamentalista (5 métodos via z-score) · 🕐 Atualizado em "
    f"**{atualizado:%d/%m/%Y %H:%M}** · preços até {precos_ate:%d/%m/%Y} · "
    f"{int(meta['n_acoes'])} ações · SELIC {meta['selic']:.1%}. "
    "Projeto educacional; não é recomendação."
)

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ações analisadas", int(meta["n_acoes"]))
c2.metric("Oportunidades (Buy)", int((gold["classificacao"] == "Buy").sum()))
c3.metric("Subvalorizadas 💎", int(gold["selo_subvalorizada"].sum()))
topo = gold.iloc[0]
c4.metric("Top do ranking", topo["ticker"], f"score {topo['score_final']:+.2f}")

st.divider()


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

# ---------- ranking ----------
st.subheader("Ranking")
vis = gold[
    ["ranking", "ticker", "setor", "selos", "score_final",
     "z_graham", "z_buffett", "z_evebitda", "z_lynch", "z_dcf", "classificacao"]
].copy()


def cor_classe(v):
    return f"color: {CORES.get(v, '#888')}; font-weight: 700"


def cor_score(v):
    return f"color: {VERDE if v >= 0 else VERMELHO}; font-weight: 700" if pd.notna(v) else ""


styled = vis.style.map(cor_classe, subset=["classificacao"]).map(
    cor_score, subset=["score_final"]
).format(
    {c: "{:+.2f}" for c in ["score_final", "z_graham", "z_buffett", "z_evebitda", "z_lynch", "z_dcf"]},
    na_rep="—",
)
st.dataframe(styled, use_container_width=True, hide_index=True, height=380)
st.caption(
    "Selos: ✅ fundamentos fortes · 💎 subvalorizada · 🛡️ risco baixo (volatilidade < mediana). "
    "score = média ponderada (pesos PRD) dos métodos disponíveis por empresa."
)

st.divider()

# ---------- drill-down por acao (Monte Carlo de valor justo) ----------
col_a, col_b = st.columns([1, 1])

with col_a:
    st.subheader("🔎 Detalhe da ação")
    tk = st.selectbox("Ação", gold["ticker"].tolist(), index=0)
    linha = gold[gold["ticker"] == tk].iloc[0]
    sil = silver[silver["ticker"] == tk].sort_values("ano")
    ult = sil.iloc[-1]

    st.markdown(
        f"**{tk}** · {linha['setor']} · classificação "
        f"<span style='color:{CORES.get(linha['classificacao'], '#888')};font-weight:700'>"
        f"{linha['classificacao']}</span> · {selos_txt(linha)}",
        unsafe_allow_html=True,
    )
    sub = pd.DataFrame(
        {"método": ["Graham", "Buffett", "EV/EBITDA", "Lynch", "DCF"],
         "z-score": [linha["z_graham"], linha["z_buffett"], linha["z_evebitda"],
                     linha["z_lynch"], linha["z_dcf"]]}
    )
    fig_sub = go.Figure(go.Bar(
        x=sub["z-score"], y=sub["método"], orientation="h",
        marker_color=[VERDE if (pd.notna(v) and v >= 0) else VERMELHO for v in sub["z-score"]],
    ))
    fig_sub.update_layout(height=240, margin=dict(l=0, r=0, t=10, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis_title="z-score (vs universo)")
    st.plotly_chart(fig_sub, use_container_width=True)

with col_b:
    st.subheader("🎲 Valor justo (Monte Carlo)")
    if ult["setor"] == "operacional" and pd.notna(ult["fco_mil"]):
        cresc = crescimento_lucro(sil["fco_mil"].tolist(), sil["ano"].tolist())
        valores = simular_valores(
            ult["fco_mil"], cresc, float(meta["selic"]),
            ult["divida_liquida_mil"], ult["acoes_circulacao_mil"],
        )
        preco = linha["preco_atual"]
        if valores.size and pd.notna(preco):
            prob = float((valores > preco).mean())
            fig = go.Figure(go.Histogram(x=valores, nbinsx=40, marker_color=VERDE, opacity=0.75))
            fig.add_vline(x=preco, line_color=VERMELHO, line_width=3,
                          annotation_text=f"preço R$ {preco:.0f}", annotation_position="top")
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis_title="valor justo por ação (R$)", yaxis_title="cenários")
            st.plotly_chart(fig, use_container_width=True)
            st.metric("Probabilidade de estar subvalorizada", f"{prob:.0%}")
        else:
            st.info("Sem valor justo calculável para esta ação.")
    else:
        st.info("Monte Carlo de valor justo só para empresas operacionais (bancos/holdings não).")

st.divider()

# ---------- risco da carteira top-N (Monte Carlo) ----------
st.subheader("🛡️ Risco da carteira top-3 (Monte Carlo, horizonte 6m)")
topn = gold.head(3)["ticker"].tolist()
ret = retornos_mensais(precos, topn)
mc = simular_carteira(ret, horizonte=6)
r1, r2, r3, r4 = st.columns(4)
r1.metric("Carteira", " · ".join(topn))
r2.metric("Retorno mediano", f"{mc['retorno_p50']:+.1%}")
r3.metric("VaR (5%)", f"{mc['var_5']:+.1%}", help="Perda no pior 5% dos cenários")
r4.metric("CVaR (5%)", f"{mc['cvar_5']:+.1%}", help="Perda esperada na cauda")
st.caption(
    "📈 (ML favorável) fica de fora dos selos: o modelo de ML, validado de forma honesta, "
    "não tem poder preditivo sobre 'bater o índice' — coerente com a expectativa do PRD."
)
