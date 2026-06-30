"""Testes do Monte Carlo (valuation e carteira)."""
import numpy as np
import pandas as pd

from src.fundamental import dcf
from src.montecarlo.portfolio import simular_carteira
from src.montecarlo.valuation import simular_valuation


def test_valuation_sem_ruido_bate_o_dcf():
    val = dcf.valor_intrinseco(100.0, 0.0, 0.10, 0.0, 10.0)
    res = simular_valuation(
        100.0, 0.0, 0.10, 0.0, 10.0, preco=val * 0.5,
        n_sim=200, sigma_cresc=0.0, sigma_selic=0.0,
    )
    assert round(res["p50"], 6) == round(val, 6)   # sem ruido -> valor pontual
    assert res["prob_subvalorizada"] == 1.0         # valor > preco sempre


def test_valuation_prob_zero_quando_caro():
    val = dcf.valor_intrinseco(100.0, 0.0, 0.10, 0.0, 10.0)
    res = simular_valuation(
        100.0, 0.0, 0.10, 0.0, 10.0, preco=val * 2,
        n_sim=200, sigma_cresc=0.0, sigma_selic=0.0,
    )
    assert res["prob_subvalorizada"] == 0.0


def test_carteira_cvar_pior_que_var_e_reprodutivel():
    rng = np.random.default_rng(0)
    ret = pd.DataFrame(rng.normal(0.01, 0.05, size=(60, 3)), columns=["A", "B", "C"])
    mc1 = simular_carteira(ret, horizonte=6, n_sim=1000, seed=7)
    mc2 = simular_carteira(ret, horizonte=6, n_sim=1000, seed=7)
    assert mc1 == mc2                          # mesma seed -> mesmo resultado
    assert mc1["cvar_5"] <= mc1["var_5"]       # cauda e pior que o percentil
    assert mc1["drawdown_medio"] <= 0
