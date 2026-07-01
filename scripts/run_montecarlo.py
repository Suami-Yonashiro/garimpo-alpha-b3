"""Monte Carlo: calcula e PERSISTE em tabelas (para o dashboard/Power BI ler).

Grava:
- gold_montecarlo_valuation : por acao operacional (P5/P50/P95 do valor justo + prob).
- gold_montecarlo_carteira  : 2500 cenarios de retorno da carteira top-N (p/ histograma).
- gold_montecarlo_carteira_resumo : mediana, VaR, CVaR, prob. de ganho da carteira.

Rodar:  PYTHONPATH=. uv run python scripts/run_montecarlo.py
"""
import numpy as np
import pandas as pd

from src.db import get_engine
from src.fundamental.lynch import crescimento_lucro
from src.montecarlo.portfolio import retornos_mensais, simular_retornos_carteira
from src.montecarlo.valuation import simular_valores

N = 3  # carteira top-N


def main() -> None:
    engine = get_engine()
    gold = pd.read_sql(
        "select ticker, setor, preco_atual, ranking from gold_fundamental_scores order by ranking",
        engine,
    )
    silver = pd.read_sql("select * from silver_fundamentals", engine)
    selic = float(pd.read_sql("select selic from meta_pipeline", engine)["selic"].iloc[0])
    precos = pd.read_sql("select ticker, data, close from bronze_prices", engine)
    precos["data"] = pd.to_datetime(precos["data"])
    latest = silver.loc[silver.groupby("ticker")["ano"].idxmax()].set_index("ticker")

    # ---- MC valuation por acao (operacionais) ----
    linhas = []
    for _, row in gold[gold["setor"] == "operacional"].iterrows():
        t, preco = row["ticker"], row["preco_atual"]
        if t not in latest.index or pd.isna(preco) or pd.isna(latest.loc[t, "fco_mil"]):
            continue
        g = silver[silver["ticker"] == t].sort_values("ano")
        v = simular_valores(
            latest.loc[t, "fco_mil"], crescimento_lucro(g["fco_mil"].tolist(), g["ano"].tolist()),
            selic, latest.loc[t, "divida_liquida_mil"], latest.loc[t, "acoes_circulacao_mil"],
        )
        if v.size == 0:
            continue
        linhas.append({
            "ticker": t, "preco": float(preco),
            "mc_p5": float(np.percentile(v, 5)), "mc_p50": float(np.percentile(v, 50)),
            "mc_p95": float(np.percentile(v, 95)),
            "prob_subvalorizada": float((v > preco).mean()),
        })
    pd.DataFrame(linhas).to_sql("gold_montecarlo_valuation", engine, if_exists="replace", index=False)

    # ---- MC carteira top-N ----
    topn = gold.head(N)["ticker"].tolist()
    finais, _ = simular_retornos_carteira(retornos_mensais(precos, topn), horizonte=6)
    rotulo = ", ".join(topn)
    pd.DataFrame({"carteira": rotulo, "retorno": finais}).to_sql(
        "gold_montecarlo_carteira", engine, if_exists="replace", index=False
    )
    var5 = float(np.percentile(finais, 5))
    pd.DataFrame([{
        "carteira": rotulo, "retorno_p50": float(np.percentile(finais, 50)),
        "var_5": var5, "cvar_5": float(finais[finais <= var5].mean()),
        "prob_ganho": float((finais > 0).mean()),
    }]).to_sql("gold_montecarlo_carteira_resumo", engine, if_exists="replace", index=False)

    print(f"gold_montecarlo_valuation: {len(linhas)} ações")
    print(f"gold_montecarlo_carteira: {len(finais)} cenários (carteira {rotulo})")


if __name__ == "__main__":
    main()
