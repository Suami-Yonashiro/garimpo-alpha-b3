"""Monte Carlo: valuation (prob. subvalorizada) + carteira (VaR/CVaR/drawdown).

Rodar:  PYTHONPATH=. uv run python scripts/run_montecarlo.py
"""
import pandas as pd

from ingestion.bcb import selic_atual
from src.db import get_engine
from src.fundamental.lynch import crescimento_lucro
from src.montecarlo.portfolio import retornos_mensais, simular_carteira
from src.montecarlo.valuation import simular_valuation

N = 3  # carteira top-N


def main() -> None:
    engine = get_engine()
    gold = pd.read_sql(
        "select ticker, setor, preco_atual, ranking from gold_fundamental_scores order by ranking",
        engine,
    )
    silver = pd.read_sql("select * from silver_fundamentals", engine)
    precos = pd.read_sql("select ticker, data, close from bronze_prices", engine)
    precos["data"] = pd.to_datetime(precos["data"])
    selic = selic_atual()

    latest = silver.loc[silver.groupby("ticker")["ano"].idxmax()].set_index("ticker")

    def cresc_fco(ticker: str) -> float | None:
        g = silver[silver["ticker"] == ticker].sort_values("ano")
        return crescimento_lucro(g["fco_mil"].tolist(), g["ano"].tolist())

    print(f"MC #1 — valuation (2500 cenarios) | SELIC {selic:.1%}\n")
    for _, row in gold[gold["setor"] == "operacional"].head(5).iterrows():
        s, t = latest.loc[row["ticker"]], row["ticker"]
        res = simular_valuation(
            s["fco_mil"], cresc_fco(t), selic, s["divida_liquida_mil"],
            s["acoes_circulacao_mil"], row["preco_atual"],
        )
        if res:
            print(f"  {t}: valor justo R$ {res['p5']:.0f}/{res['p50']:.0f}/{res['p95']:.0f} "
                  f"(P5/P50/P95) | preco R$ {row['preco_atual']:.0f} | "
                  f"P(subvalorizada) {res['prob_subvalorizada']:.0%}")

    topn = gold.head(N)["ticker"].tolist()
    ret = retornos_mensais(precos, topn)
    mc = simular_carteira(ret, horizonte=6)
    print(f"\nMC #2 — carteira top-{N} {topn} (horizonte 6m):")
    print(f"  retorno mediano {mc['retorno_p50']:+.1%} | VaR(5%) {mc['var_5']:+.1%} "
          f"| CVaR(5%) {mc['cvar_5']:+.1%} | drawdown medio {mc['drawdown_medio']:.1%}")


if __name__ == "__main__":
    main()
