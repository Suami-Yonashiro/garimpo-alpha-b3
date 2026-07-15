"""Exporta a curva completa do backtest (nao so os numeros finais), para
atualizar o grafico do post de LinkedIn sempre que o pipeline rodar de novo.

Reusa carteira_periodica do backtest.py, mas devolve a serie cumulativa por
periodo (JSON pronto pra colar nos arrays do Chart.js) em vez de so as
metricas finais (retorno acumulado, Sharpe, drawdown).

Rodar:  PYTHONPATH=. uv run python scripts/exportar_curva_backtest.py
"""
import json

import numpy as np
import pandas as pd

from src.backtest import adicionar_score_fundamental, carteira_periodica
from src.db import get_engine

N = 3
PASSO = 6


def _curva(serie: pd.Series) -> list[float]:
    """Indice acumulado (base 100), arredondado pra 1 casa -- pronto pro grafico."""
    return (np.cumprod(1 + serie.values) * 100).round(1).tolist()


def main() -> None:
    df = adicionar_score_fundamental(pd.read_sql("select * from ml_dataset", get_engine()))

    top = carteira_periodica(df, "score_fund", n=N, passo_meses=PASSO, melhores=True)
    bottom = carteira_periodica(df, "score_fund", n=N, passo_meses=PASSO, melhores=False)

    saida = {
        "datas": [d.strftime("%Y-%m") for d in top["data"]],
        "melhores": _curva(top["carteira"]),
        "ibov": _curva(top["ibov"]),
        "piores": _curva(bottom["carteira"]),
    }
    print(json.dumps(saida, ensure_ascii=False))


if __name__ == "__main__":
    main()
