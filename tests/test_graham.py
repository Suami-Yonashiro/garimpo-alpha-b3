"""Testes do metodo de Graham (funcoes puras, sem rede/banco)."""
import math

from src.fundamental.graham import classificar, margem_seguranca, valor_intrinseco


def test_valor_intrinseco_formula():
    # raiz(22.5 * 2 * 2) = raiz(90)
    assert math.isclose(valor_intrinseco(2.0, 2.0), math.sqrt(90.0))


def test_valor_intrinseco_invalido_retorna_none():
    assert valor_intrinseco(-1.0, 10.0) is None   # prejuizo
    assert valor_intrinseco(10.0, 0.0) is None     # PL zero


def test_margem_seguranca():
    # valor 100, preco 80 -> 25% de margem
    assert math.isclose(margem_seguranca(100.0, 80.0), 0.25)
    assert margem_seguranca(None, 80.0) is None


def test_classificar():
    assert classificar(0.30) == "Buy"
    assert classificar(0.10) == "Hold"
    assert classificar(0.0) == "Hold"
    assert classificar(-0.05) == "Avoid"
    assert classificar(None) == "N/A"
