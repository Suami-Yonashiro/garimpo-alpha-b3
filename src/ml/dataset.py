"""Montagem do dataset de ML (Camada 2).

Para cada (acao, fim de mes) gera uma linha com:
- features de momentum (retornos passados de 3/6/12 meses, de bronze_prices);
- features fundamentais POINT-IN-TIME (ultimo balanco com DT_RECEB <= a data);
- target binario: a acao superou o IBOV nos proximos `horizonte` meses?

A honestidade point-in-time (usar so o que era publico na data, via merge_asof na
DT_RECEB) e o que sustenta a credibilidade do modelo — ver docs/02-decisoes-adr.md.
"""
import numpy as np
import pandas as pd

from ingestion.bcb import series_macro

FEATURES_MOMENTUM = ["ret_3m", "ret_6m", "ret_12m"]
# fundamentos sempre presentes (2012+): roe, margem_liquida.
# operacionais-only (None p/ bancos -> imputados no pipeline): margem_ebitda, divida_pl, fco_receita.
FEATURES_FUND = ["roe", "margem_liquida", "margem_ebitda", "divida_pl", "fco_receita"]
FEATURES_FUND_BASE = ["roe", "margem_liquida"]  # exigidas (nao imputadas)
FEATURES_MACRO = ["selic", "ipca12", "cambio"]


def features_fundamentais(silver: pd.DataFrame) -> pd.DataFrame:
    """Deriva features fundamentais por (ticker, dt_receb) para o join point-in-time."""
    s = silver.copy()
    s["roe"] = s["lucro_liquido_mil"] / s["patrimonio_liquido_mil"]
    s["margem_liquida"] = s["lucro_liquido_mil"] / s["receita_mil"]
    s["margem_ebitda"] = s["ebitda_mil"] / s["receita_mil"]
    s["divida_pl"] = s["divida_liquida_mil"] / s["patrimonio_liquido_mil"]
    s["fco_receita"] = s["fco_mil"] / s["receita_mil"]
    s["dt_receb"] = pd.to_datetime(s["dt_receb"])
    return (
        s[["ticker", "dt_receb", *FEATURES_FUND]]
        .dropna(subset=["dt_receb"])
        .sort_values("dt_receb")
    )


def features_ticker(serie: pd.Series, ibov: pd.Series, horizonte: int) -> pd.DataFrame:
    """Momentum passado e target (vs IBOV) para uma serie mensal de precos."""
    df = pd.DataFrame(index=serie.index)
    df["close"] = serie
    df["ret_3m"] = serie.pct_change(3)
    df["ret_6m"] = serie.pct_change(6)
    df["ret_12m"] = serie.pct_change(12)

    fwd_ativo = serie.shift(-horizonte) / serie - 1
    ibov_al = ibov.reindex(serie.index)
    fwd_ibov = ibov_al.shift(-horizonte) / ibov_al - 1

    df["ret_fwd"] = fwd_ativo
    df["ret_fwd_ibov"] = fwd_ibov
    # target so onde os dois retornos futuros existem (senao NaN -> descartado)
    df["target"] = (fwd_ativo > fwd_ibov).where(fwd_ativo.notna() & fwd_ibov.notna())
    return df.reset_index(names="data")


def build_dataset(engine, horizonte_meses: int = 6) -> pd.DataFrame:
    """Monta o dataset completo (todas as acoes) e grava em ml_dataset."""
    precos = pd.read_sql("select ticker, data, close from bronze_prices", engine)
    precos["data"] = pd.to_datetime(precos["data"])
    mensal = (
        precos.pivot_table(index="data", columns="ticker", values="close")
        .sort_index()
        .resample("ME")
        .last()
    )
    ibov = mensal["IBOV"]
    fund = features_fundamentais(pd.read_sql("select * from silver_fundamentals", engine))

    partes = []
    for ticker in [c for c in mensal.columns if c != "IBOV"]:
        serie = mensal[ticker].dropna()
        f = fund[fund["ticker"] == ticker].drop(columns="ticker")
        if serie.empty or f.empty:
            continue
        df = features_ticker(serie, ibov, horizonte_meses)
        df["ticker"] = ticker
        # join point-in-time: ultimo balanco publicado ate a data
        df = pd.merge_asof(
            df.sort_values("data"), f.sort_values("dt_receb"),
            left_on="data", right_on="dt_receb", direction="backward",
        )
        partes.append(df)

    dataset = pd.concat(partes, ignore_index=True)

    # macro (mesmo para todas as acoes na data) via as-of
    macro = series_macro().reset_index(names="data")
    dataset = pd.merge_asof(
        dataset.sort_values("data"), macro.sort_values("data"),
        on="data", direction="backward",
    )

    # razoes com denominador ~0 viram inf (ex.: PL ~0) -> NaN (imputador nao trata inf)
    cols_feat = [*FEATURES_MOMENTUM, *FEATURES_FUND, *FEATURES_MACRO]
    dataset[cols_feat] = dataset[cols_feat].replace([np.inf, -np.inf], np.nan)

    # exige features SEMPRE presentes; as operacionais-only ficam NaN p/ o imputador
    obrigatorias = ["target", *FEATURES_MOMENTUM, *FEATURES_FUND_BASE, *FEATURES_MACRO]
    dataset = dataset.dropna(subset=obrigatorias)
    dataset["target"] = dataset["target"].astype(int)
    dataset["horizonte_meses"] = horizonte_meses

    dataset.to_sql("ml_dataset", engine, if_exists="replace", index=False)
    return dataset
