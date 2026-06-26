# Spike de Viabilidade de Dados — Garimpo Alpha B3

**Data:** 2026-06-25 · **Tickers de teste:** PETR4, VALE3, ITUB4
**Objetivo:** validar empiricamente, antes de construir a arquitetura, se as 3 fontes
críticas existem, são acessíveis e sustentam a tese point-in-time do projeto.

> Este documento é o **resultado** do spike (não uma suposição). Tudo aqui foi
> verificado rodando código real contra as fontes.

---

## Resumo executivo

| Fonte | Status | Papel comprovado no projeto |
|---|---|---|
| **CVM — DFP** | ✅ Viável | Fundamentos *point-in-time* (campo `DT_RECEB`) |
| **yfinance** | ✅ Viável | Preço histórico longo (backtest desde 2012) |
| **brapi.dev** | ✅ Viável (sem token p/ janela curta) | Preço corrente/diário (ferramenta viva) |

**Conclusão:** o projeto é viável. As três camadas têm fonte de dados confirmada.
Surgiram 2 complexidades reais (abaixo) que precisam entrar no dicionário de dados.

---

## 1. CVM — Demonstrações Financeiras Padronizadas (DFP)

- **URL testada:** `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2023.zip`
- **Resultado:** HTTP 200, 13,5 MB, **19 arquivos CSV** no zip (BPA, BPP, DRE, DFC, DMPL, DVA — consolidado `_con` e individual `_ind`, mais o índice).
- **Encoding:** `latin-1` · **Separador:** `;`

### 1.1 Point-in-time CONFIRMADO 🎯
O arquivo-índice `dfp_cia_aberta_2023.csv` tem as colunas:
```
CNPJ_CIA, DT_REFER, VERSAO, DENOM_CIA, CD_CVM, CATEG_DOC, ID_DOC, DT_RECEB, LINK_DOC
```
- **`DT_REFER`** = data de referência do balanço (ex.: 2023-12-31).
- **`DT_RECEB`** = **data em que a empresa entregou/divulgou à CVM** → é a âncora
  anti-look-ahead. No ML, um fundamento só pode ser "conhecido" a partir do `DT_RECEB`,
  nunca do `DT_REFER`. **Esta coluna é a fundação da honestidade do projeto.**

### 1.2 Onde está o lucro líquido
Na DRE consolidada (`dfp_cia_aberta_DRE_con_2023.csv`), a conta `3.11`
("Lucro/Prejuízo Consolidado do Período"). Ex.: Petrobras 2023 = R$ 1.153.391 (mil).

### ⚠️ Complexidade 1 — O plano de contas MUDA por setor
A amostra de contas revelou estrutura de **banco** (`3.01 = Receitas de Intermediação
Financeira`). Bancos/financeiras (ITUB4, BBAS3, etc.) têm DRE **diferente** de empresas
operacionais (PETR4, VALE3). Implicações:
- O mapa `CD_CONTA → indicador` **não é único** — precisa de um mapa por tipo de setor.
- EV/EBITDA e DCF **não se aplicam da mesma forma a bancos**. Decisão de produto:
  tratar bancos com indicadores próprios ou excluí-los de métodos incompatíveis
  (a documentar no dicionário de dados e nos ADRs).

### ⚠️ Complexidade 2 — Linhas duplicadas por empresa
Cada empresa aparece em várias linhas na DRE:
- `ORDEM_EXERC` = "ÚLTIMO" (ano corrente) vs "PENÚLTIMO" (ano anterior) — ambos no mesmo arquivo.
- `VERSAO` = reapresentações do mesmo balanço.
- **Regra de dedup necessária:** filtrar `ORDEM_EXERC = "ÚLTIMO"` e a maior `VERSAO`
  por (empresa, `DT_REFER`). Tratável, mas obrigatório.

---

## 2. yfinance — preço histórico longo

- **Teste:** download de PETR4.SA, VALE3.SA, ITUB4.SA para jan–mar/2012.
- **Resultado:** ✅ 61 pregões por ticker, com `Adj Close` (preço ajustado por
  proventos — essencial para retorno correto). Histórico desde 2012 disponível.
- **Papel:** fonte do **backtest de 13 anos**.
- **⚠️ Ressalva operacional:** sem `curl_cffi`, o Yahoo pode limitar/bloquear. Para
  baixar ~100 tickers em massa: instalar `curl_cffi`, adicionar retries + cache no Bronze.
- **⚠️ Survivorship:** yfinance não cobre deslistadas de forma confiável → confirma a
  decisão de documentar o viés em vez de caçar preços de deslistadas (ver ADR-001).

---

## 3. brapi.dev — preço corrente/diário

- **Teste:** `GET https://brapi.dev/api/quote/{TICKER}?range=1mo&interval=1d` (sem token).
- **Resultado:** ✅ HTTP 200 para os 3 tickers. Retorna `historicalDataPrice` com
  OHLCV + `adjustedClose` + preço atual e nome longo.
- **Papel:** preço **corrente/diário** da ferramenta viva (ranking do dia).
- **⚠️ Limite:** janelas longas (anos) tendem a exigir token pago. Por isso o histórico
  profundo fica com o yfinance, e o brapi com o dado do dia.

---

## Divisão de trabalho das fontes (comprovada)

| Necessidade | Fonte | Por quê |
|---|---|---|
| Fundamentos point-in-time | **CVM** | `DT_RECEB` oficial |
| Preço histórico (backtest 2012→) | **yfinance** | cobre 13 anos, `Adj Close` |
| Preço corrente (ranking diário) | **brapi** | rápido, sem token p/ janela curta |
| Macro (SELIC, IPCA, câmbio) | BCB/SGS | (não testado neste spike — baixo risco) |

---

## Ações que estes achados geram

1. **Dicionário de dados** precisa de um mapa `CD_CONTA → indicador` **por setor**
   (operacional vs financeiro), e a regra de dedup (`ORDEM_EXERC` + `VERSAO`).
2. **Ingestão de preços:** instalar `curl_cffi`; cache no Bronze; retries.
3. **ADR-001** (survivorship) e **ADR-002** (universo por liquidez point-in-time)
   confirmados pela realidade dos dados.
4. **BCB/SGS** fica como próximo mini-spike (risco baixo, `python-bcb`).
