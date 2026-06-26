"""Camada GOLD — score composto (Graham + Buffett + EV/EBITDA) e ranking.

Le silver_fundamentals, busca precos, calcula os indicadores de cada metodo e
combina tudo num score_final via z-score (src/fundamental/score.py).
"""
import pandas as pd

from ingestion.precos import precos_atuais_yf
from src.fundamental.buffett import margem_liquida, roe
from src.fundamental.ev_ebitda import enterprise_value, ev_ebitda
from src.fundamental.graham import classificar, margem_seguranca, valor_intrinseco
from src.fundamental.score import score_composto


def build_gold(engine) -> pd.DataFrame:
    silver = pd.read_sql("select * from silver_fundamentals", engine)
    precos = precos_atuais_yf(silver["ticker"].tolist())

    linhas = []
    for _, row in silver.iterrows():
        preco = precos.get(row["ticker"])
        valor = valor_intrinseco(row["lpa"], row["vpa"])
        margem = margem_seguranca(valor, preco)

        # EV/EBITDA (mesma unidade 'mil' do EBITDA: market cap = preco x acoes_mil)
        market_cap = preco * row["acoes_circulacao_mil"] if preco else None
        ev = enterprise_value(market_cap, row["divida_liquida_mil"])
        mult = ev_ebitda(ev, row["ebitda_mil"])

        linhas.append(
            {
                "ticker": row["ticker"],
                "setor": row["setor"],
                "dt_refer": row["dt_refer"],
                "preco_atual": preco,
                # Graham
                "valor_graham": valor,
                "margem_seguranca": margem,
                "classificacao": classificar(margem),
                # Buffett
                "roe": roe(row["lucro_liquido_mil"], row["patrimonio_liquido_mil"]),
                "margem_liquida": margem_liquida(row["lucro_liquido_mil"], row["receita_mil"]),
                # EV/EBITDA
                "ev_ebitda": mult,
            }
        )

    gold = score_composto(pd.DataFrame(linhas))
    gold = gold.sort_values("score_final", ascending=False, na_position="last")
    gold.insert(0, "ranking", range(1, len(gold) + 1))
    gold.to_sql("gold_fundamental_scores", engine, if_exists="replace", index=False)
    return gold
