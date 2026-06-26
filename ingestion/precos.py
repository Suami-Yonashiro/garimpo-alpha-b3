"""Precos de mercado via brapi.dev (cotacao corrente, sem token p/ uso basico).

Para o ranking do dia usamos o preco corrente. O historico longo (backtest)
usara yfinance (ver docs/02-decisoes-adr.md, ADR-004).
"""
import time

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
