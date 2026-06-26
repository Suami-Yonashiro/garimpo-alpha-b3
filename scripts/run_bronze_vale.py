"""Etapa 1 da fatia vertical — BRONZE.

Baixa da CVM os demonstrativos de VALE3 (DRE, BPP, composicao de capital) e grava
crus no Supabase, preservando a DT_RECEB (point-in-time).

Bronze = dado cru, o mais fiel possivel a fonte. Limpeza/dedup vem na Silver.
Para esta primeira fatia usamos 1 empresa e 1 ano; o loop completo (todas as
acoes, varios anos) vira na fase de ingestao do roadmap.

Rodar:  PYTHONPATH=. uv run python scripts/run_bronze_vale.py
"""
from sqlalchemy import text

from ingestion.cvm import carregar_arquivo
from src.db import get_engine

# --- alvo da fatia ---
CNPJ_VALE = "33.592.510/0001-54"
ANO = 2023

# (sufixo do arquivo na CVM, nome da tabela Bronze no Supabase)
ARQUIVOS = [
    ("DRE_con", "bronze_cvm_dre"),
    ("BPP_con", "bronze_cvm_bpp"),
    ("composicao_capital", "bronze_cvm_acoes"),
]


def main() -> None:
    engine = get_engine()
    print(f"Bronze VALE3 — ano {ANO}\n")

    for sufixo, tabela in ARQUIVOS:
        df = carregar_arquivo(ANO, sufixo, CNPJ_VALE)
        # if_exists='replace': re-rodavel sem acumular duplicatas (ok p/ a fatia).
        # Em producao o Bronze sera append-only com snapshot.
        df.to_sql(tabela, engine, if_exists="replace", index=False)
        print(f"  [OK] {sufixo:<20} -> {tabela:<20} ({len(df)} linhas gravadas)")

    # confere lendo de volta do banco (prova que gravou mesmo)
    print("\nConferindo no banco:")
    with engine.connect() as conn:
        for _, tabela in ARQUIVOS:
            n = conn.execute(text(f"select count(*) from {tabela}")).scalar()
            print(f"  {tabela:<20}: {n} linhas")


if __name__ == "__main__":
    main()
