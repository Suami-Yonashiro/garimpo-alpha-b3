"""Dashboard (fatia vertical) — mostra o score de Graham da Gold.

Rodar:  uv run streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

# permite "from src..." ao rodar via streamlit (adiciona a raiz do projeto ao path)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.db import get_engine  # noqa: E402

st.set_page_config(page_title="Garimpo Alpha B3", page_icon="📊", layout="centered")

st.title("📊 Garimpo Alpha B3")
st.caption(
    "Fatia vertical — score fundamentalista (Graham). "
    "Projeto educacional; não é recomendação de investimento."
)


@st.cache_data(ttl=300)
def carregar_gold() -> pd.DataFrame:
    return pd.read_sql("select * from gold_fundamental_scores", get_engine())


try:
    gold = carregar_gold()
except Exception as exc:  # conexao/credenciais
    st.error(f"Não consegui ler a Gold do banco: {exc}")
    st.stop()

if gold.empty:
    st.warning("Gold vazia. Rode os scripts run_bronze/silver/gold antes.")
    st.stop()

r = gold.iloc[0]
cores = {"Buy": "#16a34a", "Hold": "#d97706", "Avoid": "#dc2626", "N/A": "#6b7280"}
cor = cores.get(r["classificacao"], "#6b7280")

st.subheader(f"{r['ticker']} — referência {r['dt_refer']}")

c1, c2, c3 = st.columns(3)
c1.metric("Valor de Graham", f"R$ {r['valor_graham']:.2f}")
c2.metric("Preço atual", f"R$ {r['preco_atual']:.2f}")
c3.metric("Margem de segurança", f"{r['margem_seguranca'] * 100:.1f}%")

st.markdown(
    f"<h2 style='color:{cor};margin:0.2em 0'>{r['classificacao']}</h2>",
    unsafe_allow_html=True,
)

with st.expander("Fundamentos e dados completos"):
    st.write(f"LPA: R$ {r['lpa']:.2f}  ·  VPA: R$ {r['vpa']:.2f}")
    st.dataframe(gold, use_container_width=True)
