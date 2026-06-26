"""Metodologia de Peter Lynch (crescimento a preco razoavel).

PEG = (P/L) / crescimento de lucros (% ao ano). MENOR = melhor (paga-se pouco
por cada ponto de crescimento). PEG < 1 e classicamente atrativo.

Usa o historico de lucro (multi-ano) para estimar o crescimento via CAGR.
Nao se aplica quando o lucro inicial/atual e <= 0 ou o crescimento e negativo
(empresa nao esta "crescendo a preco razoavel") -> retorna None.
"""


def crescimento_lucro(lucros_por_ano: list[float], anos: list[int]) -> float | None:
    """CAGR do lucro do primeiro ao ultimo ano (decimal, ex.: 0.20 = 20% a.a.).

    Exige >= 2 anos e lucro inicial e final positivos (CAGR nao faz sentido
    saindo de prejuizo). Cobre o caso ciclico (ex.: VALE com prejuizo em 2019).
    """
    if len(lucros_por_ano) < 2:
        return None
    inicial, final = lucros_por_ano[0], lucros_por_ano[-1]
    n = anos[-1] - anos[0]
    if inicial <= 0 or final <= 0 or n <= 0:
        return None
    return (final / inicial) ** (1 / n) - 1


def peg(preco: float | None, lpa: float | None, crescimento: float | None) -> float | None:
    """PEG = (P/L) / crescimento_em_percentual. None se faltar dado ou crescimento <= 0."""
    if not preco or not lpa or lpa <= 0:
        return None
    if crescimento is None or crescimento <= 0:
        return None
    pl = preco / lpa
    return pl / (crescimento * 100)
