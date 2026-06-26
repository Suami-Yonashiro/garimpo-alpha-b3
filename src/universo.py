"""Universo de acoes do projeto (curado para esta fase).

Mapeia o ticker da B3 -> CNPJ (como a CVM identifica a empresa) + setor.
O 'setor' decide quais contas usar na Silver (banco x operacional; ver
docs/03-dicionario-de-dados.md). CNPJs conferidos no indice da CVM.

Mais a frente este universo sera o IBrX-100 completo (loop automatizado).
"""

# setor: "operacional" (industrial/servicos) ou "banco" (financeiro)
UNIVERSO = {
    "PETR4": {"cnpj": "33.000.167/0001-01", "setor": "operacional"},
    "VALE3": {"cnpj": "33.592.510/0001-54", "setor": "operacional"},
    "ABEV3": {"cnpj": "07.526.557/0001-00", "setor": "operacional"},
    "WEGE3": {"cnpj": "84.429.695/0001-11", "setor": "operacional"},
    "SUZB3": {"cnpj": "16.404.287/0001-55", "setor": "operacional"},
    "EGIE3": {"cnpj": "02.474.103/0001-19", "setor": "operacional"},
    "RADL3": {"cnpj": "61.585.865/0001-51", "setor": "operacional"},
    "B3SA3": {"cnpj": "09.346.601/0001-25", "setor": "operacional"},
    "ITUB4": {"cnpj": "60.872.504/0001-23", "setor": "banco"},
    "BBDC4": {"cnpj": "60.746.948/0001-12", "setor": "banco"},
}
