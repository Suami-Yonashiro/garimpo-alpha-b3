"""Metodologia de Benjamin Graham (valor intrinseco).

Valor intrinseco = raiz(22.5 * LPA * VPA), onde 22.5 = 15 (P/L max) * 1.5 (P/VP max).
Margem de seguranca = quanto o valor intrinseco esta acima do preco de mercado.

Classificacao (PRD secao 6): Buy (margem > 25%), Hold (0-25%), Avoid (< 0%).
"""
import math


def valor_intrinseco(lpa: float, vpa: float) -> float | None:
    """Valor justo de Graham. Retorna None se LPA ou VPA <= 0 (formula nao se aplica)."""
    if lpa is None or vpa is None or lpa <= 0 or vpa <= 0:
        return None
    return math.sqrt(22.5 * lpa * vpa)


def margem_seguranca(valor: float | None, preco: float) -> float | None:
    """(valor_justo - preco) / preco. Positivo = subvalorizada."""
    if valor is None or preco is None or preco <= 0:
        return None
    return (valor - preco) / preco


def classificar(margem: float | None) -> str:
    """Buy / Hold / Avoid conforme a margem de seguranca."""
    if margem is None:
        return "N/A"
    if margem > 0.25:
        return "Buy"
    if margem >= 0:
        return "Hold"
    return "Avoid"
