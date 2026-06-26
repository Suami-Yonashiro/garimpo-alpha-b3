"""Metodologia EV/EBITDA (valuation operacional).

EV (Enterprise Value) = valor de mercado + divida liquida.
EV/EBITDA = quanto se paga pela geracao de caixa operacional. MENOR = mais barato.
Nao se aplica a bancos (sem EBITDA) -> retorna None.
"""


def enterprise_value(market_cap: float | None, divida_liquida: float | None) -> float | None:
    """Valor de mercado + divida liquida (mesmas unidades, ex.: mil R$)."""
    if market_cap is None or divida_liquida is None:
        return None
    return market_cap + divida_liquida


def ev_ebitda(ev: float | None, ebitda: float | None) -> float | None:
    """EV / EBITDA. None se faltar dado ou EBITDA <= 0 (multiplo sem sentido)."""
    if ev is None or ebitda is None or ebitda <= 0:
        return None
    return ev / ebitda
