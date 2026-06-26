"""BRONZE — ingestao da CVM para todo o universo.

Baixa DRE, BPP e composicao de capital de cada empresa do universo e grava cru
no Supabase, marcando ticker e setor. Preserva a DT_RECEB (point-in-time).

Rodar:  PYTHONPATH=. uv run python scripts/run_bronze.py
"""
import pandas as pd
from sqlalchemy import text

from ingestion.cvm import carregar_arquivo
from src.db import get_engine
from src.universo import UNIVERSO

ANO = 2023
ARQUIVOS = [
    ("DRE_con", "bronze_cvm_dre"),        # resultado (lucro, receita, EBIT)
    ("BPP_con", "bronze_cvm_bpp"),         # passivo (PL, divida)
    ("BPA_con", "bronze_cvm_bpa"),         # ativo (caixa)
    ("DFC_MI_con", "bronze_cvm_dfc"),      # fluxo de caixa (D&A, FCO)
    ("composicao_capital", "bronze_cvm_acoes"),
]


def main() -> None:
    engine = get_engine()
    print(f"Bronze — universo de {len(UNIVERSO)} acoes, ano {ANO}\n")

    for sufixo, tabela in ARQUIVOS:
        frames = []
        for ticker, info in UNIVERSO.items():
            df = carregar_arquivo(ANO, sufixo, info["cnpj"])
            df.insert(0, "ticker", ticker)
            df.insert(1, "setor", info["setor"])
            frames.append(df)
        todos = pd.concat(frames, ignore_index=True)
        todos.to_sql(tabela, engine, if_exists="replace", index=False)
        print(f"  [OK] {tabela:<20} ({len(todos)} linhas de {len(frames)} empresas)")

    print("\nConferindo no banco:")
    with engine.connect() as conn:
        for _, tabela in ARQUIVOS:
            n = conn.execute(text(f"select count(*) from {tabela}")).scalar()
            print(f"  {tabela:<20}: {n} linhas")


if __name__ == "__main__":
    main()
