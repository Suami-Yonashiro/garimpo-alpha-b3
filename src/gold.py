"""Camada GOLD — score composto (Graham + Buffett + EV/EBITDA + Lynch) e ranking.

Le silver_fundamentals (historico multi-ano), busca precos, calcula os
indicadores de cada metodo e combina tudo num score_final via z-score.
"""
import datetime

import numpy as np
import pandas as pd

from ingestion.bcb import selic_atual
from src.fundamental import dcf
from src.fundamental.buffett import margem_liquida, roe
from src.fundamental.ev_ebitda import enterprise_value, ev_ebitda
from src.fundamental.graham import classificar, margem_seguranca, valor_intrinseco
from src.fundamental.lynch import crescimento_lucro, peg
from src.fundamental.score import score_composto
from src.fundamental.selos import aplicar_selos


def _cagr_por_ticker(silver: pd.DataFrame, coluna: str) -> dict[str, float | None]:
    """CAGR de uma metrica (ex.: lucro, FCO) por empresa, do historico completo."""
    saida = {}
    for ticker, g in silver.groupby("ticker"):
        g = g.sort_values("ano")
        saida[ticker] = crescimento_lucro(g[coluna].tolist(), g["ano"].tolist())
    return saida


def build_gold(engine) -> pd.DataFrame:
    silver = pd.read_sql("select * from silver_fundamentals", engine)

    # crescimentos usam o historico; o ranking usa o ano mais recente
    if "ano" in silver.columns:
        cresc_lucro = _cagr_por_ticker(silver, "lucro_liquido_mil")
        cresc_fco = _cagr_por_ticker(silver, "fco_mil")
        silver = silver.loc[silver.groupby("ticker")["ano"].idxmax()]
    else:
        cresc_lucro = cresc_fco = {}

    selic = selic_atual()  # taxa livre de risco para o WACC do DCF
    # preco atual = ultimo fechamento ja ingerido em bronze_prices (sem nova chamada de rede)
    ph = pd.read_sql("select ticker, data, close from bronze_prices", engine)
    ph["data"] = pd.to_datetime(ph["data"])
    precos = ph.sort_values("data").groupby("ticker")["close"].last().to_dict()
    # so ranqueia acoes com cotacao disponivel
    silver = silver[silver["ticker"].isin(precos)]

    # volatilidade anualizada por acao (retornos mensais) -> selo de risco
    mret = ph.pivot_table(index="data", columns="ticker", values="close").resample("ME").last().pct_change()
    vol = (mret.std() * np.sqrt(12)).to_dict()

    linhas = []
    for _, row in silver.iterrows():
        preco = precos.get(row["ticker"])
        valor = valor_intrinseco(row["lpa"], row["vpa"])
        margem = margem_seguranca(valor, preco)

        market_cap = preco * row["acoes_circulacao_mil"] if preco else None
        ev = enterprise_value(market_cap, row["divida_liquida_mil"])

        crescimento = cresc_lucro.get(row["ticker"])

        # DCF: valor justo por acao -> margem (como no Graham)
        valor_dcf = dcf.valor_intrinseco(
            row["fco_mil"], cresc_fco.get(row["ticker"]), selic,
            row["divida_liquida_mil"], row["acoes_circulacao_mil"],
        )

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
                # DCF
                "valor_dcf": valor_dcf,
                "margem_dcf": margem_seguranca(valor_dcf, preco),
                # risco
                "volatilidade": vol.get(row["ticker"]),
            }
        )

    gold = score_composto(pd.DataFrame(linhas))
    gold = aplicar_selos(gold)
    gold = gold.sort_values("score_final", ascending=False, na_position="last")
    gold.insert(0, "ranking", range(1, len(gold) + 1))
    gold.to_sql("gold_fundamental_scores", engine, if_exists="replace", index=False)

    # meta de atualizacao (orienta o analista no dashboard)
    pd.DataFrame(
        [{"atualizado_em": datetime.datetime.now(),
          "precos_ate": ph["data"].max(),
          "n_acoes": len(gold),
          "selic": selic}]
    ).to_sql("meta_pipeline", engine, if_exists="replace", index=False)
    return gold
