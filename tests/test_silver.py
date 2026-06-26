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
        ]
    )


def test_dedup_mantem_ultimo_e_maior_versao():
    d = dedup_ultimo(_dre_fake())
    assert (d["ORDEM_EXERC"] == "ÚLTIMO").all()
    assert d["VERSAO"].unique().tolist() == [2]


def test_valor_conta_pega_a_conta_certa():
    d = dedup_ultimo(_dre_fake())
    assert valor_conta(d, "3.11") == 200.0


def test_acoes_em_circulacao_desconta_tesouraria():
    acoes = pd.DataFrame(
        [{"CNPJ_CIA": "00", "QT_ACAO_TOTAL_CAP_INTEGR": 1000, "QT_ACAO_TOTAL_TESOURO": 50}]
    )
    assert acoes_em_circulacao(acoes) == 950.0


def test_calcular_indicadores_lpa_vpa():
    dre = _dre_fake()
    bpp = pd.DataFrame(
        [{"ORDEM_EXERC": "ÚLTIMO", "VERSAO": 1, "CD_CONTA": "2.03",
          "VL_CONTA": 950.0, "DT_REFER": "2023-12-31", "DT_RECEB": "2024-03-15"}]
    )
    acoes = pd.DataFrame(
        [{"CNPJ_CIA": "00", "QT_ACAO_TOTAL_CAP_INTEGR": 1000, "QT_ACAO_TOTAL_TESOURO": 50}]
    )
    ind = calcular_indicadores(dre, bpp, acoes, ticker="TEST3")
    # lucro 200 / 950 acoes
    assert round(ind["lpa"], 4) == round(200.0 / 950.0, 4)
    # PL 950 / 950 acoes = 1.0
    assert ind["vpa"] == 1.0
    assert ind["dt_receb"] == "2024-03-15"  # point-in-time veio da v2 correta
