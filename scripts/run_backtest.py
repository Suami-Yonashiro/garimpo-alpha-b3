"""Backtest top-N (ranking fundamental) vs Ibovespa desde 2013.

Rodar:  PYTHONPATH=. uv run python scripts/run_backtest.py
"""
import pandas as pd

from src.backtest import adicionar_score_fundamental, carteira_periodica, metricas
from src.db import get_engine

N = 3            # top-N acoes
PASSO = 6        # meses entre rebalanceamentos (= horizonte do retorno)


def _resumo(nome: str, serie: pd.Series, acertos: float | None = None) -> None:
    m = metricas(serie, periodos_por_ano=12 / PASSO)
    extra = f" | acerto vs IBOV: {acertos:.0%}" if acertos is not None else ""
    print(f"  {nome:<22} retorno {m['retorno_acum']:+.1%} | Sharpe {m['sharpe']:.2f} "
          f"| drawdown {m['max_drawdown']:.1%}{extra}")


def main() -> None:
    df = adicionar_score_fundamental(pd.read_sql("select * from ml_dataset", get_engine()))

    top = carteira_periodica(df, "score_fund", n=N, passo_meses=PASSO, melhores=True)
    bottom = carteira_periodica(df, "score_fund", n=N, passo_meses=PASSO, melhores=False)

    print(f"Backtest top-{N} (ranking fundamental) | {len(top)} rebalanceamentos "
          f"de {PASSO}m | {top['data'].min().date()} a {top['data'].max().date()}\n")

    acerto = (top["carteira"] > top["ibov"]).mean()
    _resumo("Carteira top-N", top["carteira"], acerto)
    _resumo("Carteira bottom-N", bottom["carteira"])
    _resumo("Ibovespa (benchmark)", top["ibov"])

    print("\nNota: 10 ações é pouco p/ conclusão estatística; backtest é demonstração.")
    print("Top-N deveria superar bottom-N se o score tiver sinal.")


if __name__ == "__main__":
    main()
