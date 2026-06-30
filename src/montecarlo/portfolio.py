"""Monte Carlo de carteira (PRD secao 8, MC #2).

Simula N cenarios de retorno conjunto dos ativos da carteira usando a matriz de
covariancia historica (preserva a CORRELACAO entre eles), compoe `horizonte`
meses e mede a distribuicao de retorno, VaR, CVaR e drawdown.
"""
import numpy as np
import pandas as pd


def retornos_mensais(precos: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Retornos mensais (fim de mes) dos tickers, a partir de bronze_prices (longo)."""
    wide = precos.pivot_table(index="data", columns="ticker", values="close")
    mensal = wide[tickers].resample("ME").last()
    return mensal.pct_change().dropna()


def simular_carteira(
    retornos: pd.DataFrame,
    pesos: np.ndarray | None = None,
    horizonte: int = 6,
    n_sim: int = 2500,
    seed: int = 42,
) -> dict:
    """Distribuicao do retorno da carteira no horizonte + VaR/CVaR/drawdown.

    VaR_5 e o 5º percentil do retorno (perda no pior 5% dos cenarios); CVaR_5 e a
    media dos retornos abaixo desse percentil (perda esperada na cauda).
    """
    n_ativos = retornos.shape[1]
    if pesos is None:
        pesos = np.full(n_ativos, 1 / n_ativos)  # equiponderado

    mu = retornos.mean().to_numpy()
    cov = retornos.cov().to_numpy()
    rng = np.random.default_rng(seed)

    # (n_sim, horizonte, n_ativos) cenarios correlacionados
    amostras = rng.multivariate_normal(mu, cov, size=(n_sim, horizonte))
    port = amostras @ pesos                      # retorno mensal da carteira
    curvas = np.cumprod(1 + port, axis=1)        # (n_sim, horizonte)
    finais = curvas[:, -1] - 1
    drawdowns = (curvas / np.maximum.accumulate(curvas, axis=1) - 1).min(axis=1)

    var5 = float(np.percentile(finais, 5))
    return {
        "retorno_p50": float(np.percentile(finais, 50)),
        "var_5": var5,
        "cvar_5": float(finais[finais <= var5].mean()),
        "drawdown_medio": float(drawdowns.mean()),
    }
