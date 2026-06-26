"""Etapa 2 da fatia vertical — SILVER.

Le o Bronze de VALE3, deriva LPA e VPA e grava em silver_fundamentals.

Rodar:  PYTHONPATH=. uv run python scripts/run_silver_vale.py
"""
from src.db import get_engine
from src.silver import build_silver_vale


def main() -> None:
    engine = get_engine()
    silver = build_silver_vale(engine)
    print("Silver gerada (silver_fundamentals):\n")
    linha = silver.iloc[0]
    print(f"  ticker            : {linha['ticker']}")
    print(f"  referencia        : {linha['dt_refer']}  (divulgado em {linha['dt_receb']})")
    print(f"  lucro liquido     : R$ {linha['lucro_liquido_mil']:,.0f} mil")
    print(f"  patrimonio liquido: R$ {linha['patrimonio_liquido_mil']:,.0f} mil")
    print(f"  acoes circulacao  : {linha['acoes_circulacao_mil']:,.0f} mil")
    print(f"  LPA               : R$ {linha['lpa']:.2f} por acao")
    print(f"  VPA               : R$ {linha['vpa']:.2f} por acao")


if __name__ == "__main__":
    main()
