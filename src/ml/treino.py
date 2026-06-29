"""Treino e validacao TEMPORAL dos modelos (Camada 2).

Validacao walk-forward (expanding window) — NUNCA k-fold aleatorio, que vazaria o
futuro no treino (criterio de qualidade nº 1 do PRD).

Como as observacoes sao mensais mas o alvo olha N meses a frente, meses vizinhos
compartilham parte do futuro (labels sobrepostos). Por isso ha um EMBARGO de N
meses entre o fim do treino e o inicio do teste (Advances in Financial ML).
"""
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score, roc_auc_score

from src.ml.dataset import FEATURES_FUND, FEATURES_MOMENTUM

FEATURES = [*FEATURES_MOMENTUM, *FEATURES_FUND]


def walk_forward_folds(datas, n_folds: int = 5, embargo_meses: int = 6):
    """Gera (mascara_treino, mascara_teste) por fold, em janela expansiva.

    O treino so usa datas anteriores a (inicio_do_teste - embargo), evitando que
    labels sobrepostos vazem do teste para o treino.
    """
    datas = pd.to_datetime(pd.Series(datas).reset_index(drop=True))
    blocos = np.array_split(np.sort(datas.unique()), n_folds + 1)
    folds = []
    for i in range(1, n_folds + 1):
        teste = blocos[i]
        embargo = pd.Timestamp(teste.min()) - pd.DateOffset(months=embargo_meses)
        folds.append(((datas < embargo).to_numpy(), datas.isin(teste).to_numpy()))
    return folds


def modelos() -> dict:
    """Os 3 algoritmos de arvore, com arvores rasas (conservador p/ pouco dado)."""
    from lightgbm import LGBMClassifier
    from sklearn.ensemble import RandomForestClassifier
    from xgboost import XGBClassifier

    return {
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=4, random_state=42, n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8,
            random_state=42, eval_metric="logloss",
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8,
            random_state=42, verbose=-1,
        ),
    }


def avaliar_walk_forward(df: pd.DataFrame, n_folds: int = 5, embargo_meses: int = 6) -> pd.DataFrame:
    """Roda a validacao temporal dos 3 modelos e retorna AUC/acuracia medios."""
    df = df.sort_values("data").reset_index(drop=True)
    X, y = df[FEATURES], df["target"]
    folds = walk_forward_folds(df["data"], n_folds, embargo_meses)

    linhas = []
    for nome, modelo in modelos().items():
        aucs, accs = [], []
        for treino, teste in folds:
            if treino.sum() == 0 or teste.sum() == 0:
                continue
            m = clone(modelo)
            m.fit(X[treino], y[treino])
            proba = m.predict_proba(X[teste])[:, 1]
            accs.append(accuracy_score(y[teste], (proba >= 0.5).astype(int)))
            if y[teste].nunique() > 1:  # AUC precisa das 2 classes no teste
                aucs.append(roc_auc_score(y[teste], proba))
        linhas.append(
            {"modelo": nome, "auc": np.mean(aucs), "acuracia": np.mean(accs),
             "folds": len(accs)}
        )
    return pd.DataFrame(linhas).sort_values("auc", ascending=False)
