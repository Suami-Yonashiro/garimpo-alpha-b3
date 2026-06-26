"""Camada GOLD — score fundamentalista pronto para consumo.

Para a fatia vertical: le silver_fundamentals, busca o preco atual e aplica o
metodo de Graham, gravando o resultado em gold_fundamental_scores.
"""
import pandas as pd

from ingestion.precos import preco_atual_brapi
from src.fundamental.graham import classificar, margem_seguranca, valor_intrinseco


def build_gold_vale(engine) -> pd.DataFrame:
    silver = pd.read_sql("select * from silver_fundamentals", engine)
    row = silver.iloc[0]

    preco = preco_atual_brapi(row["ticker"])
    valor = valor_intrinseco(row["lpa"], row["vpa"])
    margem = margem_seguranca(valor, preco)

    gold = pd.DataFrame(
        [
            {
                "ticker": row["ticker"],
                "dt_refer": row["dt_refer"],
                "lpa": row["lpa"],
                "vpa": row["vpa"],
                "valor_graham": valor,
                "preco_atual": preco,
                "margem_seguranca": margem,
                "classificacao": classificar(margem),
            }
        ]
    )
    gold.to_sql("gold_fundamental_scores", engine, if_exists="replace", index=False)
    return gold
