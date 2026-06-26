"""Testes do score composto (z-score, ponderacao e renormalizacao)."""
import math

import numpy as np
import pandas as pd

from src.fundamental.score import PESOS, score_composto, zscore


def test_zscore_media_zero_desvio_um():
    z = zscore(pd.Series([1.0, 2.0, 3.0]))
    assert math.isclose(z.mean(), 0.0, abs_tol=1e-9)
    assert math.isclose(z.iloc[2], 1.224744871, rel_tol=1e-6)  # ddof=0


def test_zscore_constante_vira_zeros():
    z = zscore(pd.Series([5.0, 5.0, 5.0]))
    assert (z == 0.0).all()


def _df_base():
    return pd.DataFrame(
        {
            "ticker": ["A", "B", "C", "D"],
            "margem_seguranca": [0.5, 0.1, -0.2, -0.4],
            "roe": [0.30, 0.20, 0.10, 0.05],
            "margem_liquida": [0.25, 0.15, 0.08, 0.02],
            "ev_ebitda": [4.0, 8.0, 12.0, np.nan],  # D sem EV/EBITDA (ex.: banco)
        }
    )


def test_score_composto_gera_subscores_e_ordena():
    out = score_composto(_df_base())
    assert {"z_graham", "z_buffett", "z_evebitda", "score_final"} <= set(out.columns)
    # A e a melhor em tudo -> maior score; ordenacao coerente
    assert out.loc[0, "score_final"] > out.loc[2, "score_final"]


def test_ev_ebitda_menor_e_melhor():
    out = score_composto(_df_base())
    # A tem o menor multiplo (4) -> z_evebitda positivo; C (12) -> negativo
    assert out.loc[0, "z_evebitda"] > out.loc[2, "z_evebitda"]


def test_renormaliza_quando_falta_metodo():
    # D nao tem EV/EBITDA: score_final deve usar so graham+buffett (sem virar NaN)
    out = score_composto(_df_base())
    score_d = out.loc[3, "score_final"]
    esperado = (
        PESOS["graham"] * out.loc[3, "z_graham"]
        + PESOS["buffett"] * out.loc[3, "z_buffett"]
    ) / (PESOS["graham"] + PESOS["buffett"])
    assert not math.isnan(score_d)
    assert math.isclose(score_d, esperado, rel_tol=1e-9)
