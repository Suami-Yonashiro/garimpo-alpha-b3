"""Universo de acoes do projeto — carteira IBrX-100 (IBXX).

Carregado de data/universo_ibrx100.csv (curado e VERSIONADO). Cada acao tem:
- cnpj            : identificador na CVM (resolvido do cadastro oficial da CVM).
- setor           : chave METODOLOGICA ("operacional" | "financeiro"). Financeiro
                    (bancos, seguradoras, holdings) NAO recebe EV/EBITDA nem DCF
                    — ver silver.py (indicadores_ev) e score.py (renormalizacao).
- setor_economico : classificacao de VITRINE (~11 setores) para o dashboard.
                    Independe do metodologico (ex.: BRAP4 = financeiro / Materiais
                    Basicos; B3SA3 = operacional / Financeiro).

Fonte dos tickers: carteira do dia da B3. Fonte de CNPJ + setor_economico:
cadastro CVM (SETOR_ATIV). Para atualizar a carteira a cada quadrimestre:
baixar a nova composicao na B3 e rodar `scripts/build_universo.py`
(a data vigente fica no cabecalho do CSV).
"""
import csv
from pathlib import Path

CAMINHO_CSV = Path(__file__).resolve().parent.parent / "data" / "universo_ibrx100.csv"


def carregar_universo(caminho: Path = CAMINHO_CSV) -> dict[str, dict]:
    """Le o CSV curado (ignorando as linhas de comentario '#') -> dict por ticker."""
    with open(caminho, encoding="utf-8") as fh:
        linhas = [ln for ln in fh if not ln.lstrip().startswith("#")]
    universo: dict[str, dict] = {}
    for row in csv.DictReader(linhas):
        universo[row["ticker"]] = {
            "cnpj": row["cnpj"],
            "setor": row["setor"],
            "setor_economico": row["setor_economico"],
        }
    return universo


UNIVERSO = carregar_universo()
