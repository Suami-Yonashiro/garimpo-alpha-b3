"""Monte Carlo de valuation (PRD secao 8, MC #1).

Em vez de um unico valor justo (DCF pontual), varia as premissas incertas
(crescimento do FCO e SELIC/WACC) em N cenarios -> DISTRIBUICAO de valor justo
-> probabilidade de a acao estar subvalorizada (valor justo > preco).
"""
import numpy as np

from src.fundamental import dcf


def simular_valuation(
    fco_base: float,
    crescimento: float | None,
    selic: float,
    divida_liquida_mil: float | None,
    acoes_mil: float | None,
    preco: float,
    n_sim: int = 2500,
    sigma_cresc: float = 0.03,
    sigma_selic: float = 0.02,
    seed: int = 42,
) -> dict | None:
    """Distribuicao do valor justo (DCF) e probabilidade de subvalorizacao."""
    rng = np.random.default_rng(seed)
    g_base = crescimento if crescimento is not None else 0.0
    cresc = np.clip(rng.normal(g_base, sigma_cresc, n_sim), 0.0, dcf.CRESCIMENTO_MAX)
    selics = np.clip(rng.normal(selic, sigma_selic, n_sim), 0.02, None)

    valores = np.array(
        [
            v
            for g, s in zip(cresc, selics)
            if (v := dcf.valor_intrinseco(fco_base, g, s, divida_liquida_mil, acoes_mil))
            is not None
        ]
    )
    if valores.size == 0:
        return None
    return {
        "p5": float(np.percentile(valores, 5)),
        "p50": float(np.percentile(valores, 50)),
        "p95": float(np.percentile(valores, 95)),
        "prob_subvalorizada": float((valores > preco).mean()),
    }
