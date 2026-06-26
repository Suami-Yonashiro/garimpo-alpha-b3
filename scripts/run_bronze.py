"""BRONZE — ingestao multi-ano da CVM para todo o universo.

Para cada ano e cada empresa, baixa DRE, BPP, BPA, DFC e composicao de capital
e grava cru no Supabase, marcando ticker, setor e ano. Preserva a DT_RECEB.

Rodar:  PYTHONPATH=. uv run python scripts/run_bronze.py
"""
import pandas as pd
from sqlalchemy import text

from ingestion.cvm import carregar_demonstrativo_ano
from src.db import get_engine
from src.universo import UNIVERSO

ANOS = range(2019, 2024)  # historico (facil de ampliar p/ 2012 quando precisar)
ARQUIVOS = [
    ("DRE_con", "bronze_cvm_dre"),        # resultado (lucro, receita, EBIT)
    ("BPP_con", "bronze_cvm_bpp"),         # passivo (PL, divida)
    ("BPA_con", "bronze_cvm_bpa"),         # ativo (caixa)
    ("DFC_MI_con", "bronze_cvm_dfc"),      # fluxo de caixa (D&A, FCO)
    ("composicao_capital", "bronze_cvm_acoes"),
]
# mapa CNPJ -> (ticker, setor) para etiquetar as linhas
POR_CNPJ = {info["cnpj"]: (tk, info["setor"]) for tk, info in UNIVERSO.items()}


def main() -> None:
    engine = get_engine()
    print(f"Bronze — {len(UNIVERSO)} acoes x {len(list(ANOS))} anos ({min(ANOS)}-{max(ANOS)})\n")

    for sufixo, tabela in ARQUIVOS:
        frames = []
        for ano in ANOS:
            try:
                completo = carregar_demonstrativo_ano(ano, sufixo)
            except KeyError:
                # alguns arquivos (ex.: composicao_capital) nao existem em anos antigos
                print(f"  [aviso] {sufixo} nao disponivel em {ano} — pulado")
                continue
            for cnpj, (ticker, setor) in POR_CNPJ.items():
                df = completo[completo["CNPJ_CIA"] == cnpj].copy()
                if df.empty:
                    continue  # empresa pode nao existir naquele ano
                df.insert(0, "ticker", ticker)
                df.insert(1, "setor", setor)
                df.insert(2, "ano", ano)
                frames.append(df)
        todos = pd.concat(frames, ignore_index=True)
        todos.to_sql(tabela, engine, if_exists="replace", index=False)
        print(f"  [OK] {tabela:<20} ({len(todos)} linhas)")

    print("\nConferindo no banco:")
    with engine.connect() as conn:
        for _, tabela in ARQUIVOS:
            n = conn.execute(text(f"select count(*) from {tabela}")).scalar()
            anos = conn.execute(text(f"select count(distinct ano) from {tabela}")).scalar()
            print(f"  {tabela:<20}: {n} linhas, {anos} anos")


if __name__ == "__main__":
    main()
