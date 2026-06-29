"""Treina e valida os 3 modelos com validacao temporal walk-forward.

Rodar:  PYTHONPATH=. uv run python scripts/run_ml_treino.py
"""
import pandas as pd

from src.db import get_engine
from src.ml.treino import FEATURES, avaliar_walk_forward


def main() -> None:
    df = pd.read_sql("select * from ml_dataset", get_engine())
    print(f"Treino sobre {len(df)} amostras | features: {FEATURES}\n")

    resultado = avaliar_walk_forward(df, n_folds=5, embargo_meses=6)
    vis = resultado.copy()
    vis["auc"] = vis["auc"].round(3)
    vis["acuracia"] = (vis["acuracia"] * 100).round(1)
    print("Validacao temporal (walk-forward, embargo 6m):")
    print(vis.to_string(index=False))

    print("\nReferencia honesta do PRD: acc 54-60%, AUC 0.55-0.62.")
    print("AUC > 0.75 ou acc > 70% = ALERTA de vazamento temporal.")


if __name__ == "__main__":
    main()
