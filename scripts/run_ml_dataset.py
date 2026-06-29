"""Monta o dataset de ML (Camada 2) e grava em ml_dataset.

Rodar:  PYTHONPATH=. uv run python scripts/run_ml_dataset.py
"""
from src.db import get_engine
from src.ml.dataset import FEATURES_FUND, FEATURES_MOMENTUM, build_dataset

HORIZONTE = 6  # meses


def main() -> None:
    ds = build_dataset(get_engine(), horizonte_meses=HORIZONTE)
    print(f"ml_dataset: {len(ds)} linhas (horizonte {HORIZONTE} meses)")
    print(f"  acoes: {ds['ticker'].nunique()} | periodo: {ds['data'].min().date()} a {ds['data'].max().date()}")
    print(f"  features: {FEATURES_MOMENTUM + FEATURES_FUND}")
    taxa = ds["target"].mean()
    print(f"  balanco do target (superou IBOV): {taxa:.1%} positivos")
    print("\n  amostras por acao:")
    print(ds.groupby("ticker").size().to_string())


if __name__ == "__main__":
    main()
