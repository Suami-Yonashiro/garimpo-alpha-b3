"""Camada SILVER — limpa o Bronze e deriva indicadores fundamentais.

Para a fatia vertical: le o Bronze de VALE3, aplica a regra de dedup obrigatoria
(ORDEM_EXERC = ULTIMO + maior VERSAO; ver docs/03-dicionario-de-dados.md) e
extrai LPA e VPA.

NOTA: VALE e empresa OPERACIONAL -> lucro liquido = conta 3.11, PL = conta 2.03.
Para bancos os codigos mudam (3.09 / 2.08). O resolvedor por setor entra quando
generalizarmos para todo o universo (item em aberto do dicionario).
"""
import pandas as pd

# codigos de conta (plano de contas CVM, empresa operacional)
CD_LUCRO_LIQUIDO = "3.11"   # Lucro/Prejuizo Consolidado do Periodo
CD_PATRIMONIO = "2.03"      # Patrimonio Liquido Consolidado


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


def acoes_em_circulacao(acoes: pd.DataFrame) -> float:
    """Acoes totais menos as em tesouraria (em milhares)."""
    a = acoes.iloc[0]
    return float(a["QT_ACAO_TOTAL_CAP_INTEGR"] - a["QT_ACAO_TOTAL_TESOURO"])


def calcular_indicadores(
    dre: pd.DataFrame, bpp: pd.DataFrame, acoes: pd.DataFrame, ticker: str
) -> dict:
    """Aplica dedup e calcula LPA e VPA a partir dos 3 demonstrativos Bronze."""
    dre_u = dedup_ultimo(dre)
    bpp_u = dedup_ultimo(bpp)

    lucro = valor_conta(dre_u, CD_LUCRO_LIQUIDO)   # em mil R$
    patrimonio = valor_conta(bpp_u, CD_PATRIMONIO)  # em mil R$
    qt_acoes = acoes_em_circulacao(acoes)           # em milhares

    # LPA e VPA: lucro/PL (mil R$) / acoes (mil) -> as unidades 'mil' se cancelam,
    # resultando em R$ por acao.
    lpa = lucro / qt_acoes
    vpa = patrimonio / qt_acoes

    return {
        "ticker": ticker,
        "cnpj": acoes.iloc[0]["CNPJ_CIA"],
        "dt_refer": dre_u["DT_REFER"].iloc[0],
        "dt_receb": dre_u["DT_RECEB"].iloc[0],   # ancora point-in-time
        "lucro_liquido_mil": lucro,
        "patrimonio_liquido_mil": patrimonio,
        "acoes_circulacao_mil": qt_acoes,
        "lpa": lpa,
        "vpa": vpa,
    }


def build_silver_vale(engine) -> pd.DataFrame:
    """Le o Bronze do banco, calcula os indicadores e grava silver_fundamentals."""
    dre = pd.read_sql("select * from bronze_cvm_dre", engine)
    bpp = pd.read_sql("select * from bronze_cvm_bpp", engine)
    acoes = pd.read_sql("select * from bronze_cvm_acoes", engine)

    indicadores = calcular_indicadores(dre, bpp, acoes, ticker="VALE3")
    silver = pd.DataFrame([indicadores])
    silver.to_sql("silver_fundamentals", engine, if_exists="replace", index=False)
    return silver
