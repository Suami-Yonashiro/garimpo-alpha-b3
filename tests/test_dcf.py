"""Testes do metodo DCF (funcoes puras)."""
import math

from src.fundamental.dcf import PREMIO_RISCO, valor_intrinseco, wacc


def test_wacc_soma_premio():
    assert math.isclose(wacc(0.10), 0.10 + PREMIO_RISCO)


def test_valor_intrinseco_positivo():
    v = valor_intrinseco(
        fco_base=100.0, crescimento=0.0, selic=0.10,
        divida_liquida_mil=0.0, acoes_mil=10.0,
    )
    assert v is not None and v > 0


def test_divida_reduz_valor():
    sem = valor_intrinseco(100.0, 0.0, 0.10, 0.0, 10.0)
    com = valor_intrinseco(100.0, 0.0, 0.10, 200.0, 10.0)  # com divida liquida
    assert com < sem


def test_none_quando_falta_dado():
    assert valor_intrinseco(None, 0.0, 0.10, 0.0, 10.0) is None      # sem FCO
    assert valor_intrinseco(-50.0, 0.0, 0.10, 0.0, 10.0) is None     # FCO negativo
    assert valor_intrinseco(100.0, 0.0, 0.10, 0.0, None) is None     # sem acoes
