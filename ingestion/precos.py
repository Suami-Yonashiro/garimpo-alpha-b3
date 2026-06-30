"""Precos de mercado via brapi.dev (cotacao corrente, sem token p/ uso basico).

Para o ranking do dia usamos o preco corrente. O historico longo (backtest)
usara yfinance (ver docs/02-decisoes-adr.md, ADR-004).
"""
import time

import pandas as pd
import requests

_UA = {"User-Agent": "Mozilla/5.0 (garimpo-alpha-b3)"}


def preco_atual_brapi(ticker: str) -> float:
    """Retorna o ultimo preco de mercado do ticker (ex.: 'VALE3')."""
    url = f"https://brapi.dev/api/quote/{ticker}"
    resp = requests.get(url, headers=_UA, timeout=30)
    resp.raise_for_status()
    resultados = resp.json().get("results") or []
    if not resultados:
        raise ValueError(f"brapi nao retornou cotacao para {ticker}")
    return float(resultados[0]["regularMarketPrice"])


def precos_atuais_yf(tickers: list[str]) -> dict[str, float]:
    """Preco atual (ultimo fechamento) via yfinance, para varios tickers de uma vez.

    Mais robusto que a brapi free para muitos tickers. Adiciona o sufixo '.SA'
    (B3) e pega o ultimo 'Close' disponivel de cada acao.
    """
    import yfinance as yf

    simbolos = {t: f"{t}.SA" for t in tickers}
    dados = yf.download(
        list(simbolos.values()), period="5d", progress=False, auto_adjust=False
    )
    fechamentos = dados["Close"]  # colunas = simbolos

    precos: dict[str, float] = {}
    for ticker, simbolo in simbolos.items():
        if simbolo in fechamentos:
            serie = fechamentos[simbolo].dropna()
            if not serie.empty:
                precos[ticker] = float(serie.iloc[-1])
    return precos


def precos_historicos_yf(
    tickers: list[str], inicio: str = "2012-01-01", tamanho_lote: int = 10
) -> pd.DataFrame:
    """Historico diario de fechamento AJUSTADO (yfinance) do universo + Ibovespa.

    Retorna formato longo: colunas ticker, data, close. O Ibovespa entra como
    ticker 'IBOV' (simbolo ^BVSP). auto_adjust=True ajusta por proventos.

    Baixa em LOTES pequenos com retry/pausa: o Yahoo throttle lotes grandes
    (tickers viram 'possibly delisted'). Lotes menores sao bem mais confiaveis.
    """
    import yfinance as yf

    simbolos = {f"{t}.SA": t for t in tickers}
    simbolos["^BVSP"] = "IBOV"
    todos = list(simbolos)

    frames = []
    for i in range(0, len(todos), tamanho_lote):
        lote = todos[i : i + tamanho_lote]
        fechamentos = pd.DataFrame()
        for _ in range(3):  # retry contra throttling
            dados = yf.download(lote, start=inicio, auto_adjust=True, progress=False)
            fechamentos = dados["Close"] if "Close" in dados else pd.DataFrame()
            faltando = [s for s in lote if s not in fechamentos.columns]
            if not faltando:
                break
            time.sleep(2)
        if fechamentos.empty:
            continue
        longo = (
            fechamentos.reset_index()
            .melt(id_vars="Date", var_name="simbolo", value_name="close")
            .dropna(subset=["close"])
        )
        frames.append(longo)
        time.sleep(1)  # gentileza entre lotes

    longo = pd.concat(frames, ignore_index=True)
    longo["ticker"] = longo["simbolo"].map(simbolos)
    return longo[["ticker", "Date", "close"]].rename(columns={"Date": "data"}).dropna(
        subset=["ticker"]
    )


def precos_atuais_brapi(tickers: list[str]) -> dict[str, float]:
    """Preco de varios tickers, UM POR REQUISICAO.

    O free tier da brapi rejeita o batch grande (varios tickers numa URL -> 401),
    mas aceita o ticker unico. Buscamos um a um e pulamos o que falhar (o ticker
    sem preco fica de fora; a Gold trata como margem indisponivel).
    """
    precos: dict[str, float] = {}
    for ticker in tickers:
        try:
            precos[ticker] = preco_atual_brapi(ticker)
            time.sleep(0.2)  # gentileza com o rate limit do free tier
        except (requests.RequestException, ValueError, KeyError) as exc:
            print(f"  [aviso] preco de {ticker} indisponivel: {exc}")
    return precos
