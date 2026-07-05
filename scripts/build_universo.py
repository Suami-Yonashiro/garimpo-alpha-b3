"""Atualiza data/universo_ibrx100.csv a partir de FONTES OFICIAIS.

Filosofia (importante): o CNPJ de uma empresa e um FATO ESTAVEL e ja verificado.
Portanto o proprio CSV curado e a fonte-da-verdade dos CNPJs. Este script:

  1. PRESERVA os CNPJs ja verificados (lidos do CSV atual);
  2. RE-DERIVA setor/setor_economico do cadastro CVM ao vivo (isso pode mudar);
  3. Para um ticker NOVO no indice (sem CNPJ conhecido), tenta casar pelo nome
     MAS o imprime como [CONFERIR] — nunca confia no fuzzy match em silencio.

Entradas:  data/raw/b3/ibrx100.csv (carteira B3) + cad_cia_aberta.csv (CVM, auto).
Saida:     data/universo_ibrx100.csv (ticker, cnpj, setor, setor_economico).

Rodar:  PYTHONPATH=. uv run python scripts/build_universo.py
"""
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parent.parent
B3_CSV = RAIZ / "data/raw/b3/ibrx100.csv"
CAD_CSV = RAIZ / "data/raw/cvm/cad_cia_aberta.csv"
CAD_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
DEST = RAIZ / "data/universo_ibrx100.csv"

# Fallback de CNPJ p/ o caso de o CSV nao existir (bootstrap). Empresas cujo nome
# curto da B3 nao casa direto com a CVM -> CNPJ conferido a mao no cadastro.
OVERRIDES = {
    "CBAV3": "61.409.892/0001-73",  # CBA = Cia Brasileira de Aluminio
    "AUAU3": "18.328.118/0001-09",  # Petz/Cobasi = Pet Center Comercio
    "VIVA3": "33.839.910/0001-11",  # Vivara Participacoes
    "CURY3": "08.797.760/0001-83",  # Cury Construtora
    "MOTV3": "02.846.056/0001-97",  # Motiva (ex-CCR)
    "B3SA3": "09.346.601/0001-25",  # B3 (nome curto demais p/ casar)
}
# Decisoes do analista p/ casos de fronteira do setor METODOLOGICO.
SETOR_OVERRIDE = {"BRAP4": "financeiro"}  # holding pura (Vale) -> sem EV/EBITDA nem DCF

FINANCEIRO = ("banco", "segurad", "intermediacao financeira", "previdencia", "securit")


def sa(s: str) -> str:
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()


def chave(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", sa(s).upper())


def setor_metodologico(setor_ativ: str) -> str:
    s = sa(setor_ativ)
    return "financeiro" if any(k in s for k in FINANCEIRO) else "operacional"


def setor_economico(ticker: str, setor_ativ: str) -> str:
    s = sa(setor_ativ)
    if any(k in s for k in ("banco", "segurad", "intermediacao financeira",
                            "previdencia", "bolsa")):
        return "Financeiro"
    if "petroleo" in s:
        return "Petroleo e Gas"
    if any(k in s for k in ("energia eletrica", "saneamento")):
        return "Utilidade Publica"
    if any(k in s for k in ("extracao mineral", "metalurgia", "siderurgia",
                            "papel e celulose", "petroquimic")):
        return "Materiais Basicos"
    if "servicos medicos" in s:
        return "Saude"
    if "telecomunica" in s:
        return "Comunicacoes"
    if "comunicacao e inform" in s:
        return "Tecnologia"
    if any(k in s for k in ("maquinas", "maqs", "equip", "veic", "transporte e logistica")):
        return "Bens Industriais"
    if any(k in s for k in ("alimentos", "bebidas", "agricultura", "farmaceutic")):
        return "Consumo nao Ciclico"
    if "comercio" in s:  # atacarejo alimentar -> nao ciclico; demais varejo -> ciclico
        return "Consumo nao Ciclico" if ticker in ("ASAI3", "GMAT3") else "Consumo Ciclico"
    if any(k in s for k in ("textil", "vestuario", "hospedagem", "turismo", "brinquedos",
                            "lazer", "educacao", "construcao civil", "const. civil",
                            "const civil", "mat. const")):
        return "Consumo Ciclico"
    if "sem setor principal" in s:  # GGPS3 (GPS) = servicos diversos
        return "Bens Industriais"
    return "Outros"


def carregar_cadastro() -> pd.DataFrame:
    if not CAD_CSV.exists():
        CAD_CSV.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(CAD_URL, headers={"User-Agent": "Mozilla/5.0 (garimpo)"}, timeout=120)
        r.raise_for_status()
        CAD_CSV.write_bytes(r.content)
    cad = pd.read_csv(CAD_CSV, sep=";", encoding="latin-1", dtype=str)
    cad["SETOR_ATIV"] = cad["SETOR_ATIV"].fillna("")
    cad["chave"] = cad["DENOM_SOCIAL"].map(chave)
    # ao deduplicar por CNPJ, prefere a linha que TEM setor preenchido
    cad["_tem_setor"] = cad["SETOR_ATIV"].str.strip().ne("")
    return cad.sort_values("_tem_setor", ascending=False).drop_duplicates("CNPJ_CIA")


def seed_cnpjs() -> dict[str, str]:
    """ticker -> cnpj JA verificados, lidos do CSV atual (fonte-da-verdade)."""
    if not DEST.exists():
        return {}
    df = pd.read_csv(DEST, comment="#", dtype=str)
    return dict(zip(df["ticker"], df["cnpj"]))


def ler_carteira_b3() -> tuple[pd.DataFrame, str]:
    with open(B3_CSV, encoding="latin-1") as fh:
        titulo = fh.readline()
    data = "?"
    if "Dia" in titulo:
        data = titulo.split("Dia")[-1].strip()
        d, m, a = (data.split("/") + ["", "", ""])[:3]
        if len(a) == 2:  # 06/07/26 -> 06/07/2026
            data = f"{d}/{m}/20{a}"
    b3 = pd.read_csv(B3_CSV, sep=";", encoding="latin-1", skiprows=1,
                     names=["ticker", "nome", "tipo", "q", "p", "x"], engine="python")
    b3["ticker"] = b3["ticker"].astype(str).str.strip()
    b3 = b3[b3["ticker"].str.match(r"^[A-Z][A-Z0-9]{3}\d+$", na=False)]  # inclui B3SA3
    b3["nome"] = b3["nome"].str.strip()
    return b3[["ticker", "nome"]].reset_index(drop=True), data


def resolver_por_nome(nome: str, cad: pd.DataFrame) -> str:
    alvo = chave(nome)
    melhor, score = None, 0.0
    for cnpj, c in zip(cad["CNPJ_CIA"], cad["chave"]):
        s = SequenceMatcher(None, alvo, c).ratio()
        if alvo and (alvo in c or c in alvo):
            s = max(s, 0.92)
        if s > score:
            melhor, score = cnpj, s
    return melhor


def main() -> None:
    cad = carregar_cadastro()
    b3, data_carteira = ler_carteira_b3()
    seed = seed_cnpjs()
    setor_por_cnpj = cad.set_index("CNPJ_CIA")["SETOR_ATIV"].to_dict()

    linhas, novos = [], []
    for _, row in b3.iterrows():
        tk, nome = row["ticker"], row["nome"]
        if tk in seed:                       # CNPJ ja verificado -> preserva
            cnpj = seed[tk]
        elif tk in OVERRIDES:                # bootstrap dos casos dificeis
            cnpj = OVERRIDES[tk]
        else:                                # ticker novo -> resolve E sinaliza
            cnpj = resolver_por_nome(nome, cad)
            novos.append((tk, nome, cnpj))
        setor_ativ = setor_por_cnpj.get(cnpj, "")
        setor = SETOR_OVERRIDE.get(tk, setor_metodologico(setor_ativ))
        linhas.append((tk, cnpj, setor, setor_economico(tk, setor_ativ)))

    final = pd.DataFrame(linhas, columns=["ticker", "cnpj", "setor", "setor_economico"])
    final = final.sort_values("ticker").reset_index(drop=True)

    cabecalho = (
        f"# Universo Garimpo Alpha B3 = carteira IBrX-100 (IBXX) de {data_carteira}\n"
        "# tickers: carteira B3 | cnpj + setor_economico: cadastro CVM (SETOR_ATIV)\n"
        "# setor (operacional/financeiro) = chave metodologica: financeiro nao recebe "
        "EV/EBITDA nem DCF\n"
        "# B3SA3=operacional (tem EBITDA), BRAP4=financeiro (holding), por decisao do analista\n"
    )
    with open(DEST, "w", encoding="utf-8", newline="") as fh:
        fh.write(cabecalho)
        final.to_csv(fh, index=False)

    print(f"OK: {len(final)} acoes ({data_carteira}) -> {DEST.relative_to(RAIZ)}")
    print(f"  operacional={sum(final.setor=='operacional')} | "
          f"financeiro={sum(final.setor=='financeiro')}")
    saiu = set(seed) - set(final["ticker"])
    if saiu:
        print(f"  [saiu do indice] {sorted(saiu)}")
    if novos:
        print("  [CONFERIR] tickers novos resolvidos por nome (verificar o CNPJ!):")
        for tk, nome, cnpj in novos:
            print(f"     {tk:8s} {nome:20s} -> {cnpj}")


if __name__ == "__main__":
    main()
