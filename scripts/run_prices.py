"""BRONZE (precos) — historico diario do universo + Ibovespa (desde 2012).

Base para os retornos futuros e o benchmark do ML/backtest (Camada 2).

Rodar:  PYTHONPATH=. uv run python scripts/run_prices.py
"""
from ingestion.precos import precos_historicos_yf
from src.db import get_engine
from src.universo import UNIVERSO


def main() -> None:
    engine = get_engine()
    df = precos_historicos_yf(list(UNIVERSO.keys()), inicio="2012-01-01")
    df.to_sql("bronze_prices", engine, if_exists="replace", index=False)

    print(f"bronze_prices: {len(df)} linhas")
    print(f"  tickers: {df['ticker'].nunique()} (inclui IBOV: {'IBOV' in df['ticker'].values})")
    print(f"  periodo: {df['data'].min().date()} a {df['data'].max().date()}")
    print("\nLinhas por ticker:")
    print(df.groupby("ticker").size().to_string())


if __name__ == "__main__":
    main()
