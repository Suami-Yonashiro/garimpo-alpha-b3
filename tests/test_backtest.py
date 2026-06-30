"""Testes do backtest (metricas e selecao top-N)."""
import math

import pandas as pd

from src.backtest import carteira_periodica, metricas


def test_metricas_retorno_e_drawdown():
    # +10%, -50%, +10%
    m = metricas([0.10, -0.50, 0.10])
    assert math.isclose(m["retorno_acum"], 1.10 * 0.50 * 1.10 - 1, rel_tol=1e-9)
    # drawdown: cai de 1.10 para 0.55 -> -50%
    assert math.isclose(m["max_drawdown"], 0.55 / 1.10 - 1, rel_tol=1e-9)


def test_metricas_sharpe_zero_quando_constante():
    import numpy as np
    assert np.isnan(metricas([0.05, 0.05, 0.05])["sharpe"])  # desvio 0


def test_carteira_seleciona_topn():
    # 1 rebalance, 4 acoes; top-2 por score devem ser as de maior ret_fwd aqui
    df = pd.DataFrame(
        {
            "data": pd.to_datetime(["2020-01-31"] * 4),
            "score_fund": [3.0, 2.0, 1.0, 0.0],
            "ret_fwd": [0.20, 0.10, -0.05, -0.10],
            "ret_fwd_ibov": [0.05] * 4,
        }
    )
    top = carteira_periodica(df, "score_fund", n=2, passo_meses=6, melhores=True)
    assert len(top) == 1
    # media dos 2 melhores scores: ret_fwd 0.20 e 0.10 -> 0.15
    assert math.isclose(top.loc[0, "carteira"], 0.15, rel_tol=1e-9)
    assert top.loc[0, "ibov"] == 0.05
