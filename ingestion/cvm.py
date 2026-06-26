"""Extracao de dados da CVM (Demonstracoes Financeiras Padronizadas - DFP).

Fonte oficial e gratuita: dados.cvm.gov.br. Cada ano e um .zip com varios CSVs
(DRE, BPP, composicao de capital, etc.) + um arquivo-indice com a DT_RECEB
(data de divulgacao = ancora point-in-time, ver docs/03-dicionario-de-dados.md).

Esta camada apenas LE e FILTRA o dado cru. Limpeza/calculo ficam na Silver/Gold.
"""
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

CVM_DFP_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS"
_UA = {"User-Agent": "Mozilla/5.0 (garimpo-alpha-b3)"}

# cache local dos zips (gitignored — ver .gitignore: data/)
CACHE_DIR = Path("data/raw/cvm")


def baixar_dfp_zip(ano: int) -> Path:
    """Baixa (e cacheia em disco) o zip da DFP de um ano. Retorna o caminho local."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    destino = CACHE_DIR / f"dfp_cia_aberta_{ano}.zip"
    if not destino.exists():
        url = f"{CVM_DFP_BASE}/dfp_cia_aberta_{ano}.zip"
        resp = requests.get(url, headers=_UA, timeout=180)
        resp.raise_for_status()
        destino.write_bytes(resp.content)
    return destino


def _ler_csv_do_zip(zip_path: Path, nome_csv: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf, zf.open(nome_csv) as fh:
        return pd.read_csv(io.BytesIO(fh.read()), sep=";", encoding="latin-1")


def _indice_dt_receb(ano: int, cnpj: str) -> pd.DataFrame:
    """Retorna DT_RECEB (data de divulgacao) por (DT_REFER, VERSAO) da empresa."""
    zp = baixar_dfp_zip(ano)
    idx = _ler_csv_do_zip(zp, f"dfp_cia_aberta_{ano}.csv")
    idx = idx[idx["CNPJ_CIA"] == cnpj]
    return idx[["DT_REFER", "VERSAO", "DT_RECEB"]].drop_duplicates()


def carregar_arquivo(ano: int, sufixo: str, cnpj: str) -> pd.DataFrame:
    """Le um demonstrativo da DFP, filtra a empresa e anexa a DT_RECEB.

    sufixo: ex. 'DRE_con', 'BPP_con', 'composicao_capital'.
    cnpj  : ex. '33.592.510/0001-54' (VALE).
    """
    zp = baixar_dfp_zip(ano)
    df = _ler_csv_do_zip(zp, f"dfp_cia_aberta_{sufixo}_{ano}.csv")
    df = df[df["CNPJ_CIA"] == cnpj].copy()
    # anexa a data de divulgacao (point-in-time) por (DT_REFER, VERSAO)
    df = df.merge(_indice_dt_receb(ano, cnpj), on=["DT_REFER", "VERSAO"], how="left")
    return df
