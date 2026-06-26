"""GOLD — score composto (Graham + Buffett) e ranking do universo.

Rodar:  PYTHONPATH=. uv run python scripts/run_gold.py
"""
from src.db import get_engine
from src.gold import build_gold


def main() -> None:
    gold = build_gold(get_engine())
    print(f"\nRanking por score composto — {len(gold)} acoes\n")
    cols = ["ranking", "ticker", "setor", "score_final", "z_graham", "z_buffett",
            "z_evebitda", "z_lynch", "peg", "classificacao"]
    vis = gold[cols].copy()
    for c in ["score_final", "z_graham", "z_buffett", "z_evebitda", "z_lynch", "peg"]:
        vis[c] = vis[c].round(2)
    print(vis.to_string(index=False))


if __name__ == "__main__":
    main()
