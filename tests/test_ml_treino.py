"""Testes da validacao temporal (walk-forward) — funcao pura, sem modelos."""
import pandas as pd

from src.ml.treino import walk_forward_folds


def test_walk_forward_respeita_ordem_e_embargo():
    datas = pd.Series(pd.date_range("2015-01-31", periods=72, freq="ME"))
    folds = walk_forward_folds(datas, n_folds=3, embargo_meses=6)
    assert len(folds) == 3

    for treino, teste in folds:
        if treino.sum() == 0:
            continue
        max_treino = datas[treino].max()
        min_teste = datas[teste].min()
        # treino sempre ANTES do teste, com pelo menos ~6 meses de embargo
        assert min_teste > max_treino
        meses = (min_teste.to_period("M") - max_treino.to_period("M")).n
        assert meses >= 6


def test_walk_forward_treino_expande():
    datas = pd.Series(pd.date_range("2015-01-31", periods=72, freq="ME"))
    folds = walk_forward_folds(datas, n_folds=3, embargo_meses=6)
    tamanhos = [treino.sum() for treino, _ in folds]
    # janela expansiva: o treino nao encolhe ao longo dos folds
    assert tamanhos == sorted(tamanhos)
