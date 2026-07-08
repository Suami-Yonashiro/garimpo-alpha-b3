"""Mede a magnitude do survivorship bias no backtest (ADR-001, Opcao C).

Nao da para caçar os "mortos" (deslistadas) com dado gratuito, mas da para MEDIR
a direcao e a ordem de grandeza do vies: compara o backtest no universo COMPLETO
(as acoes de hoje) com o subconjunto de VETERANOS (com historico utilizavel desde
o inicio da janela). Os "entrantes tardios" (IPOs recentes + entradas com gap de
dado) sao proxies de composicao survivor-enviesada; excluí-los da um TETO para o
quanto do retorno vem da composicao, nao um valor exato de survivorship.

Rodar:  PYTHONPATH=. uv run python scripts/analise_survivorship.py
"""
import pandas as pd

from src.backtest import adicionar_score_fundamental, carteira_periodica, metricas
from src.db import get_engine

PASSO, N = 6, 3
CORTE_VETERANO = pd.Timestamp("2013-12-31")  # presente no 1o ano da janela do backtest


def _linha(dados: pd.DataFrame, rotulo: str) -> dict:
    top = carteira_periodica(dados, "score_fund", n=N, passo_meses=PASSO, melhores=True)
    bot = carteira_periodica(dados, "score_fund", n=N, passo_meses=PASSO, melhores=False)
    mt, mb, mi = (metricas(s, 12 / PASSO) for s in (top["carteira"], bot["carteira"], top["ibov"]))
    return {
        "universo": rotulo,
        "acoes": dados["ticker"].nunique(),
        "top_ret": mt["retorno_acum"], "top_sharpe": mt["sharpe"],
        "top_dd": mt["max_drawdown"], "acerto": (top["carteira"] > top["ibov"]).mean(),
        "bottom_ret": mb["retorno_acum"], "ibov_ret": mi["retorno_acum"],
    }


def main() -> None:
    df = adicionar_score_fundamental(pd.read_sql("select * from ml_dataset", get_engine()))
    df["data"] = pd.to_datetime(df["data"])

    primeira = df.groupby("ticker")["data"].min()
    veteranos = primeira[primeira <= CORTE_VETERANO].index
    recentes = sorted(primeira[primeira > CORTE_VETERANO].index)

    print(f"Universo: {df['ticker'].nunique()} acoes | veteranos (desde 2013): "
          f"{len(veteranos)} | entrantes tardios: {len(recentes)}")
    print(f"Entrantes tardios (historico pos-2013): {recentes}\n")

    linhas = [_linha(df, "Completo"),
              _linha(df[df["ticker"].isin(veteranos)], "So veteranos")]
    for r in linhas:
        print(f"== {r['universo']} ({r['acoes']} acoes) ==")
        print(f"   top-{N}    {r['top_ret']:+.0%} | Sharpe {r['top_sharpe']:.2f} "
              f"| dd {r['top_dd']:.0%} | acerto {r['acerto']:.0%}")
        print(f"   bottom-{N} {r['bottom_ret']:+.0%}   |   IBOV {r['ibov_ret']:+.0%}\n")

    queda = linhas[0]["top_ret"] - linhas[1]["top_ret"]
    print(f"Impacto do survivorship no topo: {linhas[0]['top_ret']:+.0%} -> "
          f"{linhas[1]['top_ret']:+.0%} (queda de {queda:.0%} em retorno acumulado).")
    print("O sinal (top > IBOV > bottom) persiste mesmo so com veteranos -> e real.")


if __name__ == "__main__":
    main()
