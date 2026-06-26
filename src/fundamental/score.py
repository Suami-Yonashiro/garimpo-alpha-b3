"""Score composto — combina os metodos via z-score (normalizacao cruzada).

z-score: para cada metrica, quantos desvios-padrao a empresa esta acima/abaixo
da media do universo. Coloca metricas de escalas diferentes na MESMA regua.

Pesos do PRD (secao 6). Como ainda faltam Lynch e DCF, e como bancos nao tem
EV/EBITDA, o score de cada empresa e a media PONDERADA apenas dos metodos
DISPONIVEIS para ela (pesos renormalizados por linha) — exatamente o que o PRD pede.
"""
import pandas as pd

# pesos brutos do PRD; renormalizados por linha conforme os metodos disponiveis
# (faltam apenas os 0.20 do DCF para completar os 5 metodos do PRD)
PESOS = {"graham": 0.20, "buffett": 0.30, "evebitda": 0.15, "lynch": 0.15}


def zscore(serie: pd.Series) -> pd.Series:
    """(valor - media) / desvio-padrao. NaN sao ignorados no calculo e preservados."""
    desvio = serie.std(ddof=0)
    if not desvio or pd.isna(desvio):
        return pd.Series(0.0, index=serie.index)
    return (serie - serie.mean()) / desvio


def winsorizar(serie: pd.Series, limite: float = 0.01) -> pd.Series:
    """Limita outliers aos percentis [limite, 1-limite] (PRD: 1% / 99%)."""
    inf, sup = serie.quantile(limite), serie.quantile(1 - limite)
    return serie.clip(lower=inf, upper=sup)


def _media_ponderada_disponivel(row: pd.Series) -> float:
    """Media ponderada dos sub-scores nao-nulos, com pesos renormalizados."""
    colunas = {
        "graham": "z_graham",
        "buffett": "z_buffett",
        "evebitda": "z_evebitda",
        "lynch": "z_lynch",
    }
    num = den = 0.0
    for metodo, coluna in colunas.items():
        valor = row[coluna]
        if pd.notna(valor):
            num += PESOS[metodo] * valor
            den += PESOS[metodo]
    return num / den if den else float("nan")


def score_composto(df: pd.DataFrame) -> pd.DataFrame:
    """Recebe margem_seguranca, roe, margem_liquida, ev_ebitda e devolve sub-scores
    (z-score) + score_final (media ponderada dos metodos disponiveis por empresa)."""
    out = df.copy()

    # sub-score Graham: valor x preco (maior margem = melhor)
    out["z_graham"] = zscore(winsorizar(out["margem_seguranca"]))

    # sub-score Buffett: qualidade (ROE + margem liquida)
    z_roe = zscore(winsorizar(out["roe"]))
    z_margem = zscore(winsorizar(out["margem_liquida"]))
    out["z_buffett"] = (z_roe + z_margem) / 2

    # sub-score EV/EBITDA: MENOR multiplo = melhor -> inverte o sinal
    out["z_evebitda"] = -zscore(winsorizar(out["ev_ebitda"]))

    # sub-score Lynch: MENOR PEG = melhor -> inverte o sinal
    out["z_lynch"] = -zscore(winsorizar(out["peg"]))

    out["score_final"] = out.apply(_media_ponderada_disponivel, axis=1)
    return out
