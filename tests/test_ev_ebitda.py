"""Testes do metodo EV/EBITDA (funcoes puras)."""
from src.fundamental.ev_ebitda import enterprise_value, ev_ebitda


def test_enterprise_value():
    assert enterprise_value(1000.0, 200.0) == 1200.0
    assert enterprise_value(1000.0, -300.0) == 700.0   # caixa liquido reduz EV
    assert enterprise_value(None, 200.0) is None


def test_ev_ebitda():
    assert ev_ebitda(1200.0, 100.0) == 12.0
    assert ev_ebitda(1200.0, 0.0) is None     # EBITDA zero
    assert ev_ebitda(1200.0, -50.0) is None   # EBITDA negativo
    assert ev_ebitda(None, 100.0) is None
