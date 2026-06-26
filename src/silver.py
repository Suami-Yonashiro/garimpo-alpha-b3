"""Camada SILVER — limpa o Bronze e deriva indicadores fundamentais.

Le o Bronze (varias empresas), aplica a regra de dedup obrigatoria (ORDEM_EXERC =
ULTIMO + maior VERSAO; ver docs/03-dicionario-de-dados.md) e extrai LPA e VPA,
escolhendo as contas conforme o SETOR (banco x operacional).
"""
import pandas as pd

# Resolucao por DESCRICAO (robusto): o codigo do lucro/PL varia ate ENTRE bancos
# (Itau 3.09/2.08, Bradesco 3.11/2.07, VALE 3.11/2.03). A descricao e estavel.
# Receita fica pelo codigo 3.01 (consistente nos dois setores).
# Casamos sem acento por seguranca (ex.: 'quido' evita o 'i' acentuado de Liquido).
TERMOS_LUCRO = ("Lucro", "Consolidado do Per")   # Lucro/Prejuizo Consolidado do Periodo
TERMOS_PL = ("Patrim", "quido Consolidado")       # Patrimonio Liquido Consolidado
CD_RECEITA = "3.01"

# --- contas para EV/EBITDA (so empresas operacionais) ---
CD_EBIT = "3.05"               # Resultado Antes do Result. Financeiro e Tributos
CD_CAIXA = "1.01.01"           # Caixa e Equivalentes de Caixa (BPA)
CD_DIVIDA = ("2.01.04", "2.02.01")  # Emprestimos e Financiamentos (circ. + nao circ.)
TERMO_DA = "Deprecia"          # D&A na DFC: a linha de D&A contem 'Deprecia'
                               # (as '6.03.x Amortizacoes de financiamento' nao tem)


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


def valor_por_descricao(df: pd.DataFrame, *termos: str) -> float:
    """Retorna o VL_CONTA da conta cuja DS_CONTA contem TODOS os termos.

    Entre candidatas, pega o nivel mais alto (menor numero de pontos no CD_CONTA),
    evitando pegar uma sub-conta no lugar do total. Robusto a codigo variar.
    """
    mask = pd.Series(True, index=df.index)
    for termo in termos:
        mask &= df["DS_CONTA"].str.contains(termo, case=False, na=False)
    candidatas = df[mask]
    if candidatas.empty:
        raise ValueError(f"Nenhuma conta com a descricao {termos}.")
    niveis = candidatas["CD_CONTA"].str.count(r"\.")
    return float(candidatas.loc[niveis.idxmin(), "VL_CONTA"])


# Acima deste valor, o numero de acoes esta em UNIDADES (nao milhares).
# A CVM e inconsistente: VALE/ITUB reportam em milhares (~1e6-1e7), enquanto
# PETR4/WEGE3 reportam em unidades (~1e9-1e10). Empresas do IBrX tem sempre
# >~1e8 acoes reais, entao ha um vao seguro entre os dois grupos.
_LIMIAR_UNIDADES = 1e8


def valor_conta_opcional(df: pd.DataFrame, cd_conta: str, default: float = 0.0) -> float:
    """Como valor_conta, mas retorna um default se a conta nao existir."""
    linha = df[df["CD_CONTA"] == cd_conta]
    return float(linha["VL_CONTA"].iloc[0]) if not linha.empty else default


def depreciacao_amortizacao(dfc: pd.DataFrame) -> float:
    """Soma a(s) linha(s) de D&A dentro do fluxo operacional (6.01) da DFC.

    Casa por 'Deprecia' (a linha de D&A tem; as '6.03 Amortizacoes de financiamento'
    nao tem). Restringe a 6.01 para garantir que e add-back do caixa operacional.
    """
    mask = dfc["CD_CONTA"].str.startswith("6.01") & dfc["DS_CONTA"].str.contains(
        TERMO_DA, case=False, na=False
    )
    return float(dfc.loc[mask, "VL_CONTA"].sum())


def indicadores_ev(dre: pd.DataFrame, bpp: pd.DataFrame, bpa: pd.DataFrame,
                   dfc: pd.DataFrame) -> dict:
    """EBITDA e divida liquida (entradas do EV/EBITDA). So faz sentido p/ operacionais."""
    ebit = valor_conta(dre, CD_EBIT)
    da = depreciacao_amortizacao(dfc)
    divida_bruta = sum(valor_conta_opcional(bpp, cd) for cd in CD_DIVIDA)
    caixa = valor_conta_opcional(bpa, CD_CAIXA)
    return {
        "ebitda_mil": ebit + da,
        "divida_liquida_mil": divida_bruta - caixa,
    }


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
    dre: pd.DataFrame, bpp: pd.DataFrame, acoes: pd.DataFrame, ticker: str, setor: str,
    bpa: pd.DataFrame | None = None, dfc: pd.DataFrame | None = None,
) -> dict:
    """Aplica dedup e calcula LPA e VPA, resolvendo contas por descricao.

    Para empresas operacionais tambem calcula EBITDA e divida liquida (entradas
    do EV/EBITDA). Bancos nao tem EBIT/EBITDA -> esses campos ficam None.
    """
    dre_u = dedup_ultimo(dre)
    bpp_u = dedup_ultimo(bpp)

    lucro = valor_por_descricao(dre_u, *TERMOS_LUCRO)    # em mil R$
    patrimonio = valor_por_descricao(bpp_u, *TERMOS_PL)   # em mil R$
    receita = valor_conta(dre_u, CD_RECEITA)              # em mil R$
    qt_acoes = acoes_em_circulacao(acoes)                 # em milhares

    indicadores = {
        "ticker": ticker,
        "setor": setor,
        "cnpj": acoes.iloc[0]["CNPJ_CIA"],
        "dt_refer": dre_u["DT_REFER"].iloc[0],
        "dt_receb": dre_u["DT_RECEB"].iloc[0],   # ancora point-in-time
        "lucro_liquido_mil": lucro,
        "patrimonio_liquido_mil": patrimonio,
        "receita_mil": receita,
        "acoes_circulacao_mil": qt_acoes,
        "lpa": lucro / qt_acoes,   # 'mil' se cancela -> R$ por acao
        "vpa": patrimonio / qt_acoes,
        "ebitda_mil": None,
        "divida_liquida_mil": None,
    }

    # EV/EBITDA so para operacionais (banco nao tem EBIT)
    if setor == "operacional" and bpa is not None and dfc is not None:
        indicadores.update(indicadores_ev(dre_u, bpp_u, dedup_ultimo(bpa), dedup_ultimo(dfc)))

    return indicadores


def build_silver(engine, universo: dict) -> pd.DataFrame:
    """Le o Bronze do banco, calcula indicadores por empresa e grava a Silver."""
    dre = pd.read_sql("select * from bronze_cvm_dre", engine)
    bpp = pd.read_sql("select * from bronze_cvm_bpp", engine)
    bpa = pd.read_sql("select * from bronze_cvm_bpa", engine)
    dfc = pd.read_sql("select * from bronze_cvm_dfc", engine)
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
                bpa=bpa[bpa["ticker"] == ticker],
                dfc=dfc[dfc["ticker"] == ticker],
            )
            linhas.append(ind)
        except (ValueError, IndexError) as exc:
            print(f"  [aviso] {ticker} pulado: {exc}")

    silver = pd.DataFrame(linhas)
    silver.to_sql("silver_fundamentals", engine, if_exists="replace", index=False)
    return silver
