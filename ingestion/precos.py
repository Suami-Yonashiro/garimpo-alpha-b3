"""Precos de mercado via brapi.dev (cotacao corrente, sem token p/ uso basico).

Para o ranking do dia usamos o preco corrente. O historico longo (backtest)
usara yfinance (ver docs/02-decisoes-adr.md, ADR-004).
"""
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
