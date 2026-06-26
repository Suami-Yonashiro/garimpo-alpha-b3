"""Testes do metodo Peter Lynch (PEG e crescimento)."""
import math

from src.fundamental.lynch import crescimento_lucro, peg


def test_crescimento_lucro_cagr():
    # 100 -> 200 em 2 anos -> CAGR = sqrt(2)-1 ~ 0.4142
    c = crescimento_lucro([100.0, 150.0, 200.0], [2021, 2022, 2023])
    assert math.isclose(c, math.sqrt(2) - 1, rel_tol=1e-6)


def test_crescimento_invalido_quando_sai_de_prejuizo():
    # lucro inicial negativo (ciclica) -> CAGR nao se aplica
    assert crescimento_lucro([-50.0, 200.0], [2022, 2023]) is None
    assert crescimento_lucro([100.0], [2023]) is None  # 1 ano so


def test_peg():
    # P/L = 100/10 = 10; crescimento 20% -> PEG = 10/20 = 0.5
    assert peg(100.0, 10.0, 0.20) == 0.5
    assert peg(100.0, 10.0, -0.05) is None   # crescimento negativo
    assert peg(100.0, 0.0, 0.20) is None     # LPA invalido
    assert peg(None, 10.0, 0.20) is None     # sem preco
