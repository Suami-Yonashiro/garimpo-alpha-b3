"""Metodologia de Warren Buffett (qualidade do negocio).

Captura empresas que geram retorno alto e consistente sobre o capital.
Versao desta fase: ROE e margem liquida (indicadores que ja temos do dado CVM).
ROIC e Divida/Patrimonio ficam para quando mapearmos as contas de divida
(ver itens em aberto em docs/03-dicionario-de-dados.md).
"""


def roe(lucro_liquido: float, patrimonio_liquido: float) -> float | None:
    """Retorno sobre o patrimonio = lucro liquido / patrimonio liquido."""
    if patrimonio_liquido is None or patrimonio_liquido <= 0:
        return None
    return lucro_liquido / patrimonio_liquido


def margem_liquida(lucro_liquido: float, receita: float) -> float | None:
    """Margem liquida = lucro liquido / receita."""
    if receita is None or receita <= 0:
        return None
    return lucro_liquido / receita
