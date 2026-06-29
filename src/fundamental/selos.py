"""Selos da visao final integrada (PRD secao 9).

Selos sao mais interpretaveis e honestos que um unico numero. Por enquanto, os
dois que a Camada 1 ja permite calcular:
- ✅ Fundamentos fortes: score_final no topo do universo (percentil alto).
- 💎 Subvalorizada: preco abaixo do valor justo (margem de Graham ou DCF positiva).

Os selos 📈 (ML favoravel) e 🛡️ (risco baixo) chegam com as Camadas 2 e 3.
"""
import pandas as pd


def aplicar_selos(gold: pd.DataFrame, percentil_forte: float = 0.70) -> pd.DataFrame:
    """Adiciona colunas booleanas selo_fundamentos e selo_subvalorizada."""
    out = gold.copy()

    # ✅ fundamentos fortes: score no topo (>= percentil)
    limiar = out["score_final"].quantile(percentil_forte)
    out["selo_fundamentos"] = out["score_final"] >= limiar

    # 💎 subvalorizada: ao menos um valor justo (Graham ou DCF) acima do preco
    margem_graham = out["margem_seguranca"].fillna(-1.0)
    if "margem_dcf" in out.columns:
        margem_dcf = out["margem_dcf"].fillna(-1.0)
    else:
        margem_dcf = pd.Series(-1.0, index=out.index)
    out["selo_subvalorizada"] = (margem_graham > 0) | (margem_dcf > 0)

    return out
