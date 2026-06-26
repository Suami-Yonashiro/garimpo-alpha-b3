"""Camada GOLD — score composto (Graham + Buffett + EV/EBITDA + Lynch) e ranking.

Le silver_fundamentals (historico multi-ano), busca precos, calcula os
indicadores de cada metodo e combina tudo num score_final via z-score.
"""
import pandas as pd

from ingestion.precos import precos_atuais_yf
from src.fundamental.buffett import margem_liquida, roe
from src.fundamental.ev_ebitda import enterprise_value, ev_ebitda
from src.fundamental.graham import classificar, margem_seguranca, valor_intrinseco
from src.fundamental.lynch import crescimento_lucro, peg
from src.fundamental.score import score_composto


def _crescimentos_por_ticker(silver: pd.DataFrame) -> dict[str, float | None]:
    """CAGR de lucro de cada empresa, a partir do historico completo."""
    crescimentos = {}
    for ticker, g in silver.groupby("ticker"):
        g = g.sort_values("ano")
        crescimentos[ticker] = crescimento_lucro(
            g["lucro_liquido_mil"].tolist(), g["ano"].tolist()
        )
    return crescimentos


def build_gold(engine) -> pd.DataFrame:
    silver = pd.read_sql("select * from silver_fundamentals", engine)

    # crescimento (Lynch) usa o historico; o ranking usa o ano mais recente
    crescimentos = _crescimentos_por_ticker(silver) if "ano" in silver.columns else {}
    if "ano" in silver.columns:
        silver = silver.loc[silver.groupby("ticker")["ano"].idxmax()]

    precos = precos_atuais_yf(silver["ticker"].tolist())

    linhas = []
    for _, row in silver.iterrows():
        preco = precos.get(row["ticker"])
        valor = valor_intrinseco(row["lpa"], row["vpa"])
        margem = margem_seguranca(valor, preco)

        market_cap = preco * row["acoes_circulacao_mil"] if preco else None
        ev = enterprise_value(market_cap, row["divida_liquida_mil"])

        crescimento = crescimentos.get(row["ticker"])

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
                "ev_ebitda": ev_ebitda(ev, row["ebitda_mil"]),
                # Lynch
                "crescimento_lucro": crescimento,
                "peg": peg(preco, row["lpa"], crescimento),
            }
        )

    gold = score_composto(pd.DataFrame(linhas))
    gold = gold.sort_values("score_final", ascending=False, na_position="last")
    gold.insert(0, "ranking", range(1, len(gold) + 1))
    gold.to_sql("gold_fundamental_scores", engine, if_exists="replace", index=False)
    return gold
