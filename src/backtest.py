"""Backtest da estrategia top-N vs Ibovespa (PRD secao 7.4).

Reusa o painel point-in-time do ml_dataset (que ja traz o retorno futuro de cada
acao e do IBOV). A cada `passo` meses, rankeia por um score, compra as top-N
(equiponderado), segura `passo` meses (periodos NAO sobrepostos) e compara com o
Ibovespa. Metricas: retorno acumulado, Sharpe, max drawdown, taxa de acerto.
"""
import numpy as np
import pandas as pd


def _z(s: pd.Series) -> pd.Series:
    desvio = s.std(ddof=0)
    return (s - s.mean()) / desvio if desvio else s * 0.0


def adicionar_score_fundamental(df: pd.DataFrame) -> pd.DataFrame:
    """Score fundamental cross-sectional por mes: qualidade - alavancagem."""
    out = df.copy()

    def por_mes(g: pd.DataFrame) -> pd.Series:
        return (
            _z(g["roe"])
            + _z(g["margem_liquida"])
            + _z(g["fco_receita"].fillna(g["fco_receita"].median()))
            - _z(g["divida_pl"].fillna(g["divida_pl"].median()))
        )

    out["score_fund"] = out.groupby("data", group_keys=False).apply(por_mes)
    return out


def carteira_periodica(
    df: pd.DataFrame, score_col: str, n: int = 3, passo_meses: int = 6, melhores: bool = True
) -> pd.DataFrame:
    """Retornos por periodo de rebalanceamento da carteira top-N (ou bottom-N)."""
    df = df.sort_values("data")
    datas_rb = np.sort(df["data"].unique())[::passo_meses]  # nao sobreposto

    linhas = []
    for d in datas_rb:
        g = df[df["data"] == d]
        if g.empty:
            continue
        escolhidas = g.nlargest(n, score_col) if melhores else g.nsmallest(n, score_col)
        linhas.append(
            {"data": d, "carteira": escolhidas["ret_fwd"].mean(),
             "ibov": g["ret_fwd_ibov"].iloc[0]}
        )
    return pd.DataFrame(linhas)


def metricas(retornos: pd.Series, periodos_por_ano: float = 2.0) -> dict:
    """Retorno acumulado, Sharpe (anualizado) e max drawdown de uma serie de retornos."""
    r = np.asarray(retornos, dtype=float)
    curva = np.cumprod(1 + r)
    drawdown = (curva / np.maximum.accumulate(curva) - 1).min()
    desvio = r.std(ddof=0)
    # tolerancia: 0.05 nao e exato em float -> std ~1e-18, nao zero
    sharpe = (r.mean() / desvio) * np.sqrt(periodos_por_ano) if desvio > 1e-12 else np.nan
    return {
        "retorno_acum": curva[-1] - 1 if len(r) else np.nan,
        "sharpe": sharpe,
        "max_drawdown": drawdown,
    }
