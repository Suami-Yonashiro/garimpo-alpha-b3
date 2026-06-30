"""Dashboard — Garimpo Alpha B3.

Storytelling do macro ao especifico: visao geral -> ranking -> detalhe da acao
-> risco de carteira. Base clara, cor com funcao, explicacao sob cada titulo.

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

# paleta: accent indigo p/ interface; verde/ambar/vermelho com funcao (dados)
INDIGO, VERDE, AMBAR, VERMELHO = "#4F46E5", "#16A34A", "#D97706", "#DC2626"
TINTA, CINZA, GRID = "#0F172A", "#64748B", "#E2E8F0"
CORES_CLASSE = {"Buy": VERDE, "Hold": AMBAR, "Avoid": VERMELHO, "N/A": CINZA}


def estilo(fig: go.Figure, altura: int = 280) -> go.Figure:
    fig.update_layout(
        height=altura, margin=dict(l=10, r=10, t=10, b=30), bargap=0.08,
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

# ====================== cabecalho (titulo esq. / data dir.) ======================
atualizado = pd.to_datetime(meta["atualizado_em"])
precos_ate = pd.to_datetime(meta["precos_ate"])
ch1, ch2 = st.columns([3, 1])
with ch1:
    st.title("Garimpo Alpha B3")
with ch2:
    st.markdown(
        f"<div style='text-align:right;color:{CINZA};font-size:0.85rem;padding-top:1.4rem'>"
        f"Atualizado em<br><b style='color:{TINTA};font-size:1.0rem'>{atualizado:%d/%m/%Y %H:%M}</b>"
        f"<br>preços até {precos_ate:%d/%m/%Y} · {int(meta['n_acoes'])} ações</div>",
        unsafe_allow_html=True,
    )
st.markdown(
    f"<span style='color:{CINZA}'>Ranqueamento de ações da B3 por fundamentos, com "
    "valuation e risco probabilísticos. Projeto educacional — não é recomendação de "
    "investimento.</span>",
    unsafe_allow_html=True,
)
st.write("")

# ====================== visao geral (KPIs) ======================
k1, k2, k3, k4 = st.columns(4)
k1.metric("Ações analisadas", int(meta["n_acoes"]))
k2.metric("Oportunidades (Buy)", int((gold["classificacao"] == "Buy").sum()))
k3.metric("Subvalorizadas", int(gold["selo_subvalorizada"].sum()))
topo = gold.iloc[0]
k4.metric("1º do ranking", topo["ticker"], f"score {topo['score_final']:+.2f}")

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

# ====================== ranking ======================
st.subheader("Ranking de ações")
st.caption(
    "Cada ação recebe um **score** que combina 5 métodos fundamentalistas (Graham, "
    "Buffett, EV/EBITDA, Lynch e DCF), padronizados e comparados entre si. Quanto maior "
    "o score, melhor posicionada. Os **selos** resumem: ✅ fundamentos fortes · "
    "💎 preço abaixo do valor justo · 🛡️ risco (volatilidade) abaixo da mediana."
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
st.dataframe(styled, use_container_width=True, hide_index=True, height=400)

st.divider()

# ====================== detalhe da acao ======================
st.subheader("Detalhe da ação")
st.caption(
    "Selecione uma ação para ver **como ela pontua em cada método** e a **faixa de valor "
    "justo** estimada por simulação. A leitura: barras à direita (verde) = ponto forte; "
    "à esquerda (vermelho) = ponto fraco, sempre em relação à média do universo."
)
tk = st.selectbox("Ação", gold["ticker"].tolist(), index=0, label_visibility="collapsed")
linha = gold[gold["ticker"] == tk].iloc[0]
sil = silver[silver["ticker"] == tk].sort_values("ano")
ult = sil.iloc[-1]

col_a, col_b = st.columns([1, 1])
with col_a:
    st.markdown(
        f"**{tk}** · {linha['setor']} · "
        f"<span style='color:{CORES_CLASSE.get(linha['classificacao'], CINZA)};font-weight:700'>"
        f"{linha['classificacao']}</span> &nbsp; {selos_txt(linha)}",
        unsafe_allow_html=True,
    )
    metodos = ["Graham", "Buffett", "EV/EBITDA", "Lynch", "DCF"]
    zs = [linha["z_graham"], linha["z_buffett"], linha["z_evebitda"], linha["z_lynch"], linha["z_dcf"]]
    fig = go.Figure(go.Bar(
        x=zs, y=metodos, orientation="h",
        marker_color=[VERDE if (pd.notna(v) and v >= 0) else VERMELHO for v in zs],
    ))
    fig.update_layout(xaxis_title="z-score (desvios vs. média do universo)")
    st.plotly_chart(estilo(fig, 260), use_container_width=True)

with col_b:
    if ult["setor"] == "operacional" and pd.notna(ult["fco_mil"]):
        cresc = crescimento_lucro(sil["fco_mil"].tolist(), sil["ano"].tolist())
        valores = simular_valores(
            ult["fco_mil"], cresc, float(meta["selic"]),
            ult["divida_liquida_mil"], ult["acoes_circulacao_mil"],
        )
        preco = linha["preco_atual"]
        if valores.size and pd.notna(preco):
            prob = float((valores > preco).mean())
            fig2 = go.Figure(go.Histogram(x=valores, nbinsx=40, marker_color=INDIGO, opacity=0.8))
            fig2.add_vline(x=preco, line_color=VERMELHO, line_width=3,
                           annotation_text=f"preço R$ {preco:.0f}", annotation_position="top")
            fig2.update_layout(xaxis_title="valor justo estimado por ação (R$)",
                               yaxis_title="nº de cenários")
            st.plotly_chart(estilo(fig2, 260), use_container_width=True)
            st.markdown(
                f"**{prob:.0%}** dos 2.500 cenários apontam valor justo **acima** do preço "
                f"atual — ou seja, {prob:.0%} de chance de estar subvalorizada."
            )
        else:
            st.info("Sem valor justo calculável para esta ação.")
    else:
        st.info(
            "Valuation por fluxo de caixa (DCF/Monte Carlo) se aplica a empresas "
            "operacionais — bancos e holdings usam outra lógica."
        )

st.divider()

# ====================== risco da carteira ======================
st.subheader("E se eu investir nas 3 melhores? (risco em 6 meses)")
topn = gold.head(3)["ticker"].tolist()
st.caption(
    f"Simulamos **2.500 cenários** para os próximos **6 meses** de uma carteira dividida "
    f"igualmente entre as 3 primeiras do ranking ({', '.join(topn)}). O gráfico mostra "
    "todos os resultados possíveis; as faixas abaixo traduzem o que esperar — inclusive "
    "no pior caso."
)
finais, _ = simular_retornos_carteira(retornos_mensais(precos, topn), horizonte=6)
mediana = float(pd.Series(finais).median())
p95 = float(pd.Series(finais).quantile(0.95))
var5 = float(pd.Series(finais).quantile(0.05))
cvar5 = float(finais[finais <= var5].mean())

m1, m2, m3 = st.columns(3)
m1.metric("Cenário típico (mediana)", f"{mediana:+.1%}")
m2.metric("Cenário otimista (5% melhores)", f"{p95:+.1%}")
m3.metric("Cenário pessimista (5% piores)", f"{var5:+.1%}",
          help="VaR: perda que só é superada em 5% dos casos. "
               f"Na média desses piores casos (CVaR), a perda é {cvar5:+.1%}.")

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
    f"no cenário típico rende **{mediana:+.1%}** em 6 meses, mas num cenário ruim (5% "
    f"piores) a perda chega a **{var5:.1%}** ou mais. Use isso para dimensionar quanto "
    "está disposto a arriscar."
)
st.caption(
    "Nota: o modelo de ML (probabilidade de superar o índice) foi validado de forma "
    "honesta e **não** tem poder preditivo — por isso não há selo 📈; o sucesso do "
    "produto vem do processo e do backtest, não de previsão mágica."
)
