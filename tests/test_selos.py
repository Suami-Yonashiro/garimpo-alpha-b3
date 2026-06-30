"""Testes dos selos da visao integrada."""
import pandas as pd

from src.fundamental.selos import aplicar_selos


def test_selos():
    df = pd.DataFrame(
        {
            "score_final": [2.0, 1.0, 0.0, -1.0, -2.0],
            "margem_seguranca": [0.3, -0.1, 0.2, -0.5, None],
            "margem_dcf": [0.1, -0.2, -0.1, -0.3, 0.4],
            "volatilidade": [0.20, 0.50, 0.30, 0.60, 0.10],
        }
    )
    out = aplicar_selos(df, percentil_forte=0.70)

    # fundamentos fortes: score no topo do universo
    assert out.loc[0, "selo_fundamentos"]        # maior score
    assert not out.loc[4, "selo_fundamentos"]    # menor score

    # subvalorizada: Graham OU DCF positivo
    assert out.loc[0, "selo_subvalorizada"]      # ambos > 0
    assert out.loc[2, "selo_subvalorizada"]      # graham 0.2 > 0
    assert not out.loc[3, "selo_subvalorizada"]  # ambos < 0
    assert out.loc[4, "selo_subvalorizada"]      # dcf 0.4 > 0 (graham None)

    # risco baixo: volatilidade <= mediana (0.30)
    assert out.loc[0, "selo_risco_baixo"]        # 0.20 <= 0.30
    assert not out.loc[1, "selo_risco_baixo"]    # 0.50 > 0.30
    assert out.loc[4, "selo_risco_baixo"]        # 0.10 <= 0.30
