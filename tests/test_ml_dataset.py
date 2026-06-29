"""Testes da montagem do dataset de ML (funcoes puras)."""
import pandas as pd

from src.ml.dataset import features_fundamentais, features_ticker


def test_features_ticker_momentum_e_target():
    idx = pd.date_range("2020-01-31", periods=8, freq="ME")
    serie = pd.Series([10, 11, 12, 13, 14, 15, 16, 17], index=idx, dtype=float)  # subindo
    ibov = pd.Series([100.0] * 8, index=idx)  # flat
    df = features_ticker(serie, ibov, horizonte=2)

    # momentum: ret_3m na 4a obs = 13/10 - 1
    assert round(df.loc[3, "ret_3m"], 4) == round(13 / 10 - 1, 4)

    # target: acao subindo vs IBOV flat -> sempre supera (onde ha futuro)
    validas = df.dropna(subset=["target"])
    assert (validas["target"] == 1).all()
    # ultimas linhas sem futuro suficiente -> target NaN
    assert df["target"].isna().sum() == 2  # horizonte=2


def test_target_zero_quando_perde_do_ibov():
    idx = pd.date_range("2020-01-31", periods=5, freq="ME")
    serie = pd.Series([10.0] * 5, index=idx)        # flat
    ibov = pd.Series([10, 11, 12, 13, 14], index=idx, dtype=float)  # IBOV subindo
    df = features_ticker(serie, ibov, horizonte=1)
    validas = df.dropna(subset=["target"])
    assert (validas["target"] == 0).all()  # acao flat perde do IBOV em alta


def test_features_fundamentais_deriva_roe_e_margem():
    silver = pd.DataFrame(
        {
            "ticker": ["X"],
            "dt_receb": ["2023-03-15"],
            "lucro_liquido_mil": [200.0],
            "patrimonio_liquido_mil": [1000.0],
            "receita_mil": [800.0],
        }
    )
    f = features_fundamentais(silver)
    assert round(f.loc[0, "roe"], 4) == 0.2          # 200/1000
    assert round(f.loc[0, "margem_liquida"], 4) == 0.25  # 200/800
    assert f.loc[0, "dt_receb"] == pd.Timestamp("2023-03-15")
