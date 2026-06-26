"""Score composto — combina os metodos via z-score (normalizacao cruzada).

z-score: para cada metrica, quantos desvios-padrao a empresa esta acima/abaixo
da media do universo. Coloca metricas de escalas diferentes (margem de Graham %,
ROE, margem liquida) na MESMA regua, permitindo somar com pesos.

Pesos (PRD secao 6) renormalizados para os metodos disponiveis nesta fase:
Buffett 30% + Graham 20% -> Buffett 0.60, Graham 0.40.
"""
import pandas as pd

PESOS = {"graham": 0.40, "buffett": 0.60}


def zscore(serie: pd.Series) -> pd.Series:
    """(valor - media) / desvio-padrao. Se desvio 0/NaN, retorna zeros."""
    desvio = serie.std(ddof=0)
    if not desvio or pd.isna(desvio):
        return pd.Series(0.0, index=serie.index)
    return (serie - serie.mean()) / desvio


def winsorizar(serie: pd.Series, limite: float = 0.01) -> pd.Series:
    """Limita outliers aos percentis [limite, 1-limite] (PRD: 1% / 99%)."""
    inf, sup = serie.quantile(limite), serie.quantile(1 - limite)
    return serie.clip(lower=inf, upper=sup)


def score_composto(df: pd.DataFrame) -> pd.DataFrame:
    """Recebe colunas margem_seguranca, roe, margem_liquida e devolve sub-scores
    (z-score) + score_final ponderado. Buffett = media de z(ROE) e z(margem)."""
    out = df.copy()

    # sub-score Graham: valor x preco (margem de seguranca)
    out["z_graham"] = zscore(winsorizar(out["margem_seguranca"]))

    # sub-score Buffett: qualidade (ROE + margem liquida)
    z_roe = zscore(winsorizar(out["roe"]))
    z_margem = zscore(winsorizar(out["margem_liquida"]))
    out["z_buffett"] = (z_roe + z_margem) / 2

    out["score_final"] = (
        PESOS["graham"] * out["z_graham"] + PESOS["buffett"] * out["z_buffett"]
    )
    return out
