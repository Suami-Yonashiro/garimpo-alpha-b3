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
    "Ranking fundamentalista — score composto dos 5 métodos (Graham, Buffett, "
    "EV/EBITDA, Lynch, DCF) via z-score. Projeto educacional; não é recomendação."
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

# --- selos (✅ fundamentos fortes, 💎 subvalorizada) ---
def montar_selos(row: pd.Series) -> str:
    s = []
    if row.get("selo_fundamentos"):
        s.append("✅")
    if row.get("selo_subvalorizada"):
        s.append("💎")
    return " ".join(s)


gold["selos"] = gold.apply(montar_selos, axis=1)

# --- KPIs ---
topo = gold.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ações analisadas", len(gold))
c2.metric("Oportunidades (Buy)", int((gold["classificacao"] == "Buy").sum()))
c3.metric("Subvalorizadas 💎", int(gold["selo_subvalorizada"].sum()))
c4.metric("Top do ranking", f"{topo['ticker']}", f"score {topo['score_final']:+.2f}")

st.divider()

# --- Tabela de ranking (por score composto) ---
vis = gold[
    ["ranking", "ticker", "setor", "selos", "score_final", "z_graham", "z_buffett",
     "z_evebitda", "z_lynch", "z_dcf", "classificacao"]
].copy()


def colorir_classe(valor: str) -> str:
    return f"color: {CORES.get(valor, '#888')}; font-weight: 700"


def colorir_score(valor: float) -> str:
    if pd.isna(valor):
        return ""
    return f"color: {'#16C784' if valor >= 0 else '#dc2626'}; font-weight: 700"


styled = (
    vis.style
    .map(colorir_classe, subset=["classificacao"])
    .map(colorir_score, subset=["score_final"])
    .format(
        {c: "{:+.2f}" for c in
         ["score_final", "z_graham", "z_buffett", "z_evebitda", "z_lynch", "z_dcf"]},
        na_rep="—",
    )
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.caption(
    "**Selos:** ✅ fundamentos fortes (score no topo) · 💎 subvalorizada (preço < valor justo). "
    "📈 ML e 🛡️ risco chegam nas Camadas 2 e 3.  ·  "
    "score_final = média ponderada (pesos do PRD) dos métodos disponíveis por empresa, "
    "renormalizados — bancos não têm EV/EBITDA nem DCF; cíclicas não têm Lynch. "
    "z = desvios-padrão vs. a média do universo (EV/EBITDA e Lynch invertidos: menor = melhor)."
)
