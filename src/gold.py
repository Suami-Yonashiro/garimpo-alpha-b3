"""Camada GOLD — score fundamentalista pronto para consumo (ranking).

Le silver_fundamentals (varias empresas), busca os precos atuais e aplica o
metodo de Graham, gerando um RANKING por margem de seguranca em
gold_fundamental_scores.
"""
import pandas as pd

from ingestion.precos import precos_atuais_yf
from src.fundamental.graham import classificar, margem_seguranca, valor_intrinseco


def build_gold(engine) -> pd.DataFrame:
    silver = pd.read_sql("select * from silver_fundamentals", engine)
    precos = precos_atuais_yf(silver["ticker"].tolist())

    linhas = []
    for _, row in silver.iterrows():
        preco = precos.get(row["ticker"])
        valor = valor_intrinseco(row["lpa"], row["vpa"])
        margem = margem_seguranca(valor, preco)
        linhas.append(
            {
                "ticker": row["ticker"],
                "setor": row["setor"],
                "dt_refer": row["dt_refer"],
                "lpa": row["lpa"],
                "vpa": row["vpa"],
                "valor_graham": valor,
                "preco_atual": preco,
                "margem_seguranca": margem,
                "classificacao": classificar(margem),
            }
        )

    gold = pd.DataFrame(linhas).sort_values(
        "margem_seguranca", ascending=False, na_position="last"
    )
    gold.insert(0, "ranking", range(1, len(gold) + 1))
    gold.to_sql("gold_fundamental_scores", engine, if_exists="replace", index=False)
    return gold
