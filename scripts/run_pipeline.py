"""Pipeline fim-a-fim: roda todas as etapas em ordem, com um comando.

Base para automacao (cron/Prefect chamam este script). Cada etapa e um script
independente; o meta de atualizacao e gravado pelo run_gold.

Rodar:  PYTHONPATH=. uv run python scripts/run_pipeline.py
"""
import subprocess
import sys
from pathlib import Path

# ordem das etapas (cada uma le do banco o que a anterior gravou)
ETAPAS = [
    ("Bronze CVM", "run_bronze.py"),
    ("Bronze precos", "run_prices.py"),
    ("Silver", "run_silver.py"),
    ("Gold (+ meta de atualizacao)", "run_gold.py"),
    ("Monte Carlo (tabelas)", "run_montecarlo.py"),
    ("Dataset ML", "run_ml_dataset.py"),
]

RAIZ = Path(__file__).resolve().parent.parent


def main() -> None:
    for i, (nome, script) in enumerate(ETAPAS, 1):
        print(f"\n{'=' * 60}\n[{i}/{len(ETAPAS)}] {nome}\n{'=' * 60}")
        env = {"PYTHONPATH": str(RAIZ)}
        r = subprocess.run(
            [sys.executable, str(RAIZ / "scripts" / script)],
            cwd=RAIZ, env={**__import__("os").environ, **env},
        )
        if r.returncode != 0:
            print(f"\n[ERRO] Etapa '{nome}' falhou (codigo {r.returncode}). Pipeline abortado.")
            sys.exit(r.returncode)
    print("\nPipeline concluido com sucesso.")


if __name__ == "__main__":
    main()
