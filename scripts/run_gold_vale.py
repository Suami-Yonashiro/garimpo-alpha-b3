"""Etapa 3 da fatia vertical — GOLD.

Le a Silver, busca o preco atual e calcula o score de Graham de VALE3.

Rodar:  PYTHONPATH=. uv run python scripts/run_gold_vale.py
"""
from src.db import get_engine
from src.gold import build_gold_vale


def main() -> None:
    engine = get_engine()
    gold = build_gold_vale(engine)
    r = gold.iloc[0]
    print("Gold gerada (gold_fundamental_scores):\n")
    print(f"  ticker            : {r['ticker']}")
    print(f"  LPA / VPA         : R$ {r['lpa']:.2f} / R$ {r['vpa']:.2f}")
    print(f"  valor Graham      : R$ {r['valor_graham']:.2f}")
    print(f"  preco atual       : R$ {r['preco_atual']:.2f}")
    print(f"  margem seguranca  : {r['margem_seguranca'] * 100:.1f}%")
    print(f"  classificacao     : {r['classificacao']}")


if __name__ == "__main__":
    main()
