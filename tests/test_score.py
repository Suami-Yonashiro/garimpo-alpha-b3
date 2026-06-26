"""Testes do score composto (z-score e ponderacao)."""
import math

import pandas as pd

from src.fundamental.score import PESOS, score_composto, zscore


def test_zscore_media_zero_desvio_um():
    z = zscore(pd.Series([1.0, 2.0, 3.0]))
    assert math.isclose(z.mean(), 0.0, abs_tol=1e-9)
    # desvio populacional (ddof=0): valores -1.2247, 0, 1.2247
    assert math.isclose(z.iloc[2], 1.224744871, rel_tol=1e-6)


def test_zscore_constante_vira_zeros():
    z = zscore(pd.Series([5.0, 5.0, 5.0]))
    assert (z == 0.0).all()


def test_score_composto_pondera_e_ordena_metricas():
    df = pd.DataFrame(
        {
            "ticker": ["A", "B", "C"],
            "margem_seguranca": [0.5, 0.0, -0.5],
            "roe": [0.30, 0.15, 0.05],
            "margem_liquida": [0.25, 0.10, 0.02],
        }
    )
    out = score_composto(df)
    assert {"z_graham", "z_buffett", "score_final"} <= set(out.columns)
    # A e a melhor em tudo -> maior score_final; C a pior -> menor
    assert out.loc[0, "score_final"] > out.loc[2, "score_final"]
    # pesos somam 1
    assert math.isclose(PESOS["graham"] + PESOS["buffett"], 1.0)
