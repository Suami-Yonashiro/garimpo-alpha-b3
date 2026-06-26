"""SILVER — deriva LPA e VPA do universo a partir do Bronze.

Rodar:  PYTHONPATH=. uv run python scripts/run_silver.py
"""
from src.db import get_engine
from src.silver import build_silver
from src.universo import UNIVERSO


def main() -> None:
    silver = build_silver(get_engine(), UNIVERSO)
    print(f"\nSilver gerada: {len(silver)} empresas\n")
    cols = ["ticker", "setor", "lpa", "vpa"]
    print(silver[cols].to_string(index=False))


if __name__ == "__main__":
    main()
