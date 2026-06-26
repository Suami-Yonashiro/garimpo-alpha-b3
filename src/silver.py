"""Camada SILVER — limpa o Bronze e deriva indicadores fundamentais.

Le o Bronze (varias empresas), aplica a regra de dedup obrigatoria (ORDEM_EXERC =
ULTIMO + maior VERSAO; ver docs/03-dicionario-de-dados.md) e extrai LPA e VPA,
escolhendo as contas conforme o SETOR (banco x operacional).
"""
import pandas as pd

# codigos de conta por setor (plano de contas CVM; ver dicionario de dados)
# 'receita' = 3.01 nos dois setores (Receita de Venda / Receitas de Interm. Financeira)
CONTAS_POR_SETOR = {
    "operacional": {"lucro": "3.11", "pl": "2.03", "receita": "3.01"},
    "banco": {"lucro": "3.09", "pl": "2.08", "receita": "3.01"},
}


def dedup_ultimo(df: pd.DataFrame) -> pd.DataFrame:
    """Mantem so o exercicio corrente (ULTIMO) e a versao mais recente.

    CUIDADO: 'PENULTIMO' tambem contem 'ULTIMO' -> filtramos contendo 'LTIMO'
    mas EXCLUINDO 'PEN' (robusto a acento). Sem isso, o ano anterior vaza.
    """
    eh_ultimo = df["ORDEM_EXERC"].str.contains("LTIMO", na=False)
    eh_penultimo = df["ORDEM_EXERC"].str.contains("PEN", na=False)
    d = df[eh_ultimo & ~eh_penultimo]
    if "VERSAO" in d.columns and not d.empty:
        d = d[d["VERSAO"] == d["VERSAO"].max()]
    return d


def valor_conta(df: pd.DataFrame, cd_conta: str) -> float:
    """Retorna o VL_CONTA de uma conta especifica (erro claro se nao achar)."""
    linha = df[df["CD_CONTA"] == cd_conta]
    if linha.empty:
        raise ValueError(f"Conta {cd_conta} nao encontrada no demonstrativo.")
    return float(linha["VL_CONTA"].iloc[0])


# Acima deste valor, o numero de acoes esta em UNIDADES (nao milhares).
# A CVM e inconsistente: VALE/ITUB reportam em milhares (~1e6-1e7), enquanto
# PETR4/WEGE3 reportam em unidades (~1e9-1e10). Empresas do IBrX tem sempre
# >~1e8 acoes reais, entao ha um vao seguro entre os dois grupos.
_LIMIAR_UNIDADES = 1e8


def acoes_em_circulacao(acoes: pd.DataFrame) -> float:
    """Acoes em circulacao (totais - tesouraria), padronizadas em MILHARES.

    Normaliza a inconsistencia de unidade da CVM: se o total esta em unidades
    (>= limiar), divide total e tesouraria por 1000 para virar milhares.
    """
    a = acoes.iloc[0]
    total = float(a["QT_ACAO_TOTAL_CAP_INTEGR"])
    tesouro = float(a["QT_ACAO_TOTAL_TESOURO"])
    fator = 1000.0 if total >= _LIMIAR_UNIDADES else 1.0
    return (total - tesouro) / fator


def calcular_indicadores(
    dre: pd.DataFrame, bpp: pd.DataFrame, acoes: pd.DataFrame, ticker: str, setor: str
) -> dict:
    """Aplica dedup e calcula LPA e VPA, escolhendo as contas pelo setor."""
    if setor not in CONTAS_POR_SETOR:
        raise ValueError(f"Setor desconhecido: {setor}")
    contas = CONTAS_POR_SETOR[setor]

    dre_u = dedup_ultimo(dre)
    bpp_u = dedup_ultimo(bpp)

    lucro = valor_conta(dre_u, contas["lucro"])      # em mil R$
    patrimonio = valor_conta(bpp_u, contas["pl"])     # em mil R$
    receita = valor_conta(dre_u, contas["receita"])   # em mil R$
    qt_acoes = acoes_em_circulacao(acoes)             # em milhares

    # LPA/VPA: as unidades 'mil' se cancelam -> R$ por acao.
    return {
        "ticker": ticker,
        "setor": setor,
        "cnpj": acoes.iloc[0]["CNPJ_CIA"],
        "dt_refer": dre_u["DT_REFER"].iloc[0],
        "dt_receb": dre_u["DT_RECEB"].iloc[0],   # ancora point-in-time
        "lucro_liquido_mil": lucro,
        "patrimonio_liquido_mil": patrimonio,
        "receita_mil": receita,
        "acoes_circulacao_mil": qt_acoes,
        "lpa": lucro / qt_acoes,
        "vpa": patrimonio / qt_acoes,
    }


def build_silver(engine, universo: dict) -> pd.DataFrame:
    """Le o Bronze do banco, calcula indicadores por empresa e grava a Silver."""
    dre = pd.read_sql("select * from bronze_cvm_dre", engine)
    bpp = pd.read_sql("select * from bronze_cvm_bpp", engine)
    acoes = pd.read_sql("select * from bronze_cvm_acoes", engine)

    linhas = []
    for ticker, info in universo.items():
        try:
            ind = calcular_indicadores(
                dre[dre["ticker"] == ticker],
                bpp[bpp["ticker"] == ticker],
                acoes[acoes["ticker"] == ticker],
                ticker=ticker,
                setor=info["setor"],
            )
            linhas.append(ind)
        except (ValueError, IndexError) as exc:
            print(f"  [aviso] {ticker} pulado: {exc}")

    silver = pd.DataFrame(linhas)
    silver.to_sql("silver_fundamentals", engine, if_exists="replace", index=False)
    return silver
