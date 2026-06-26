"""Testes da camada Silver — usam dados sinteticos (nao precisam de banco)."""
import pandas as pd

from src.silver import (
    acoes_em_circulacao,
    calcular_indicadores,
    dedup_ultimo,
    valor_conta,
)


def _dre_fake():
    return pd.DataFrame(
        [
            # exercicio anterior (deve ser descartado pelo dedup)
            {"ORDEM_EXERC": "PENÚLTIMO", "VERSAO": 1, "CD_CONTA": "3.11",
             "VL_CONTA": 100.0, "DT_REFER": "2022-12-31", "DT_RECEB": "2023-03-01"},
            # versao antiga (deve perder para a v2)
            {"ORDEM_EXERC": "ÚLTIMO", "VERSAO": 1, "CD_CONTA": "3.11",
             "VL_CONTA": 180.0, "DT_REFER": "2023-12-31", "DT_RECEB": "2024-02-20"},
            # versao mais recente (deve vencer)
            {"ORDEM_EXERC": "ÚLTIMO", "VERSAO": 2, "CD_CONTA": "3.11",
             "VL_CONTA": 200.0, "DT_REFER": "2023-12-31", "DT_RECEB": "2024-03-15"},
            # ANO ANTERIOR com a MESMA versao da vencedora: nao pode vazar
            # ('PENÚLTIMO' contem 'ÚLTIMO' -> pega o bug do contains ingênuo)
            {"ORDEM_EXERC": "PENÚLTIMO", "VERSAO": 2, "CD_CONTA": "3.11",
             "VL_CONTA": 999.0, "DT_REFER": "2022-12-31", "DT_RECEB": "2023-03-01"},
            # receita (3.01), necessaria para a margem liquida
            {"ORDEM_EXERC": "ÚLTIMO", "VERSAO": 2, "CD_CONTA": "3.01",
             "VL_CONTA": 1000.0, "DT_REFER": "2023-12-31", "DT_RECEB": "2024-03-15"},
        ]
    )


def test_dedup_mantem_ultimo_e_maior_versao():
    d = dedup_ultimo(_dre_fake())
    assert (d["ORDEM_EXERC"] == "ÚLTIMO").all()
    assert d["VERSAO"].unique().tolist() == [2]


def test_valor_conta_pega_a_conta_certa():
    d = dedup_ultimo(_dre_fake())
    assert valor_conta(d, "3.11") == 200.0


def test_acoes_em_circulacao_em_milhares_mantem():
    # valor pequeno (ja em milhares) -> nao normaliza
    acoes = pd.DataFrame(
        [{"CNPJ_CIA": "00", "QT_ACAO_TOTAL_CAP_INTEGR": 1000, "QT_ACAO_TOTAL_TESOURO": 50}]
    )
    assert acoes_em_circulacao(acoes) == 950.0


def test_acoes_em_circulacao_em_unidades_normaliza():
    # valor grande (em unidades) -> divide por 1000 para virar milhares
    acoes = pd.DataFrame(
        [{"CNPJ_CIA": "00", "QT_ACAO_TOTAL_CAP_INTEGR": 13_000_000_000,
          "QT_ACAO_TOTAL_TESOURO": 100_000_000}]
    )
    # (13e9 - 100e6) / 1000 = 12_900_000 (milhares)
    assert acoes_em_circulacao(acoes) == 12_900_000.0


def test_calcular_indicadores_operacional():
    dre = _dre_fake()  # conta 3.11 (operacional)
    bpp = pd.DataFrame(
        [{"ORDEM_EXERC": "ÚLTIMO", "VERSAO": 1, "CD_CONTA": "2.03",
          "VL_CONTA": 950.0, "DT_REFER": "2023-12-31", "DT_RECEB": "2024-03-15"}]
    )
    acoes = pd.DataFrame(
        [{"CNPJ_CIA": "00", "QT_ACAO_TOTAL_CAP_INTEGR": 1000, "QT_ACAO_TOTAL_TESOURO": 50}]
    )
    ind = calcular_indicadores(dre, bpp, acoes, ticker="TEST3", setor="operacional")
    assert round(ind["lpa"], 4) == round(200.0 / 950.0, 4)  # lucro 200 / 950
    assert ind["vpa"] == 1.0                                  # PL 950 / 950
    assert ind["dt_receb"] == "2024-03-15"                    # point-in-time correto


def test_calcular_indicadores_banco_usa_contas_diferentes():
    # banco: lucro = 3.09, PL = 2.08 (e NAO 3.11 / 2.03); receita = 3.01
    dre = pd.DataFrame(
        [
            {"ORDEM_EXERC": "ÚLTIMO", "VERSAO": 1, "CD_CONTA": "3.09",
             "VL_CONTA": 300.0, "DT_REFER": "2023-12-31", "DT_RECEB": "2024-02-10"},
            {"ORDEM_EXERC": "ÚLTIMO", "VERSAO": 1, "CD_CONTA": "3.01",
             "VL_CONTA": 1500.0, "DT_REFER": "2023-12-31", "DT_RECEB": "2024-02-10"},
        ]
    )
    bpp = pd.DataFrame(
        [{"ORDEM_EXERC": "ÚLTIMO", "VERSAO": 1, "CD_CONTA": "2.08",
          "VL_CONTA": 600.0, "DT_REFER": "2023-12-31", "DT_RECEB": "2024-02-10"}]
    )
    acoes = pd.DataFrame(
        [{"CNPJ_CIA": "00", "QT_ACAO_TOTAL_CAP_INTEGR": 300, "QT_ACAO_TOTAL_TESOURO": 0}]
    )
    ind = calcular_indicadores(dre, bpp, acoes, ticker="BANK4", setor="banco")
    assert ind["lpa"] == 1.0   # 300 / 300
    assert ind["vpa"] == 2.0   # 600 / 300
