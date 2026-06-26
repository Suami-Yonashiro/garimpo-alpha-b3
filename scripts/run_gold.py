"""GOLD — ranking fundamentalista (Graham) do universo.

Rodar:  PYTHONPATH=. uv run python scripts/run_gold.py
"""
from src.db import get_engine
from src.gold import build_gold


def main() -> None:
    gold = build_gold(get_engine())
    print(f"\nRanking Graham — {len(gold)} acoes\n")
    cols = ["ranking", "ticker", "setor", "valor_graham", "preco_atual",
            "margem_seguranca", "classificacao"]
    vis = gold[cols].copy()
    vis["margem_seguranca"] = (vis["margem_seguranca"] * 100).round(1)
    vis["valor_graham"] = vis["valor_graham"].round(2)
    print(vis.to_string(index=False))


if __name__ == "__main__":
    main()
