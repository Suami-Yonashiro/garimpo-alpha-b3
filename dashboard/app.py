"""Dashboard — ranking fundamentalista (Graham) do universo.

Rodar:  uv run streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

# permite "from src..." ao rodar via streamlit (adiciona a raiz do projeto ao path)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.db import get_engine  # noqa: E402

st.set_page_config(page_title="Garimpo Alpha B3", page_icon="📊", layout="wide")

CORES = {"Buy": "#16a34a", "Hold": "#d97706", "Avoid": "#dc2626", "N/A": "#6b7280"}

st.title("📊 Garimpo Alpha B3")
st.caption(
    "Ranking fundamentalista — score composto (Graham + Buffett, via z-score). "
    "Projeto educacional; não é recomendação de investimento."
)


@st.cache_data(ttl=300)
def carregar_gold() -> pd.DataFrame:
    return pd.read_sql("select * from gold_fundamental_scores order by ranking", get_engine())


try:
    gold = carregar_gold()
except Exception as exc:
    st.error(f"Não consegui ler a Gold do banco: {exc}")
    st.stop()

if gold.empty:
    st.warning("Gold vazia. Rode os scripts run_bronze/silver/gold antes.")
    st.stop()

# --- KPIs ---
n_total = len(gold)
n_buy = int((gold["classificacao"] == "Buy").sum())
topo = gold.iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric("Ações analisadas", n_total)
c2.metric("Oportunidades (Buy)", n_buy)
c3.metric("Top do ranking", f"{topo['ticker']}  (score {topo['score_final']:.2f})")

st.divider()

# --- Tabela de ranking (por score composto) ---
vis = gold[
    ["ranking", "ticker", "setor", "score_final", "z_graham", "z_buffett",
     "roe", "margem_liquida", "classificacao"]
].copy()


def colorir_classe(valor: str) -> str:
    return f"color: {CORES.get(valor, '#888')}; font-weight: 700"


styled = (
    vis.style.map(colorir_classe, subset=["classificacao"]).format(
        {
            "score_final": "{:.2f}",
            "z_graham": "{:+.2f}",
            "z_buffett": "{:+.2f}",
            "roe": "{:.1%}",
            "margem_liquida": "{:.1%}",
        }
    )
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.caption(
    "score_final = 0,40·z(Graham) + 0,60·z(Buffett). z = desvios-padrão acima/abaixo "
    "da média do universo. 'classificação' reflete a margem de Graham. "
    "Faltam EV/EBITDA, Lynch e DCF (e os pesos finais do PRD)."
)
