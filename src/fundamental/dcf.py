"""Metodologia DCF (Fluxo de Caixa Descontado) — padronizada e conservadora.

Versao deliberadamente simples e transparente (PRD secao 6):
- Fluxo base = FCO (caixa das operacoes) do ano corrente.
- Crescimento explicito = crescimento historico do FCO, LIMITADO a [0, 8%].
- WACC = SELIC (livre de risco) + premio de risco fixo.
- Perpetuidade conservadora (g_perp fixo, sempre < WACC).
- Valor da empresa - divida liquida = valor do equity -> valor justo por acao.

Nao se aplica a bancos (FCO/valuation operacional nao e padrao) -> usado so p/ operacionais.
"""

PREMIO_RISCO = 0.05        # premio de risco fixo somado a SELIC
ANOS_PROJECAO = 5          # horizonte explicito
G_PERPETUIDADE = 0.03      # crescimento na perpetuidade (conservador)
CRESCIMENTO_MAX = 0.08     # teto conservador para o crescimento explicito


def wacc(selic: float) -> float:
    """Taxa de desconto = SELIC + premio de risco fixo."""
    return selic + PREMIO_RISCO


def valor_intrinseco(
    fco_base: float | None,
    crescimento: float | None,
    selic: float,
    divida_liquida_mil: float | None,
    acoes_mil: float | None,
) -> float | None:
    """Valor justo por acao pelo DCF. None se faltar dado essencial."""
    if not fco_base or fco_base <= 0 or not acoes_mil or acoes_mil <= 0:
        return None
    taxa = wacc(selic)
    if taxa <= G_PERPETUIDADE:
        return None

    # crescimento conservador: limitado a [0, CRESCIMENTO_MAX]; None -> 0
    g = max(0.0, min(crescimento if crescimento is not None else 0.0, CRESCIMENTO_MAX))

    # fluxos explicitos descontados
    valor_presente = 0.0
    fco = fco_base
    for t in range(1, ANOS_PROJECAO + 1):
        fco *= 1 + g
        valor_presente += fco / (1 + taxa) ** t

    # valor terminal (Gordon) descontado
    terminal = fco * (1 + G_PERPETUIDADE) / (taxa - G_PERPETUIDADE)
    valor_presente += terminal / (1 + taxa) ** ANOS_PROJECAO

    # valor da empresa (mil R$) -> equity -> por acao (mil/mil se cancela -> R$/acao)
    equity = valor_presente - (divida_liquida_mil or 0.0)
    return equity / acoes_mil
