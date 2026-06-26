"""Testes do metodo Buffett (funcoes puras)."""
from src.fundamental.buffett import margem_liquida, roe


def test_roe():
    assert roe(100.0, 200.0) == 0.5
    assert roe(100.0, 0.0) is None       # PL zero
    assert roe(100.0, -10.0) is None     # PL negativo


def test_margem_liquida():
    assert margem_liquida(20.0, 100.0) == 0.2
    assert margem_liquida(20.0, 0.0) is None
