# Dicionário de Dados — CVM (DFP/ITR) → Indicadores

**Data:** 2026-06-25 · **Base da verificação:** DFP 2023, empresas VALE (industrial) e
ITAÚ UNIBANCO (banco). Todos os códigos abaixo foram **conferidos com dados reais** no spike.

> **Por que este documento existe:** o spike provou que o plano de contas da CVM **muda
> conforme o setor**. Mapear "código de conta → indicador" errado é a falha silenciosa
> mais perigosa do projeto (o lucro de um banco viria errado e ninguém perceberia). Este
> dicionário é a fonte única de verdade desse mapeamento.

---

## 0. Convenções e cuidados gerais

- **Encoding:** `latin-1` · **Separador:** `;` · **Escala:** valores em **mil reais**
  (`ESCALA_MOEDA = MIL`); nº de ações também em **milhares**.
- **Consolidado vs Individual:** usar **consolidado** (`_con`) para holdings; cair para
  individual (`_ind`) só quando não houver consolidado.
- **Regra de dedup (OBRIGATÓRIA)** — cada empresa aparece em várias linhas:
  1. filtrar `ORDEM_EXERC = "ÚLTIMO"` (descarta o ano anterior que vem junto);
  2. manter a maior `VERSAO` por (`CNPJ_CIA`, `DT_REFER`) — descarta reapresentações antigas.
- **Resolução por DESCRIÇÃO, não só por código:** como o código muda por setor, o método
  mais robusto é casar por `DS_CONTA` (texto padronizado e estável) e usar o `CD_CONTA`
  como confirmação. Ex.: `DS_CONTA == "Lucro/Prejuízo Consolidado do Período"`.

---

## 1. Chave point-in-time (a mais importante)

| Campo | Arquivo | Significado | Uso |
|---|---|---|---|
| `DT_REFER` | índice + todos | Data de referência do balanço (ex.: 2023-12-31) | Período do dado |
| **`DT_RECEB`** | `dfp_cia_aberta_2023.csv` (índice) | **Data de entrega/divulgação à CVM** | **Âncora anti-look-ahead.** Um fundamento só "existe" para o ML a partir desta data. |
| `VERSAO` | todos | Versão do documento | Dedup (maior vence) |
| `CD_CVM` / `CNPJ_CIA` | todos | Identificador da empresa | Join entre arquivos e com preços |

> **Regra de ouro do ML:** ao montar features para uma data `t`, só pode usar fundamentos
> com `DT_RECEB <= t`. Nunca `DT_REFER <= t` (o balanço de 31/12 só é público em ~março).

---

## 2. Mapa indicador → conta, POR SETOR

Legenda: 🏭 = empresa operacional (VALE, PETR4…) · 🏦 = banco/financeira (ITUB4, BBAS3…)

### 2.1 Demonstração de Resultado (DRE — arquivo `..._DRE_con_...`)

| Indicador | 🏭 Industrial | 🏦 Banco | Observação |
|---|---|---|---|
| Receita | `3.01` Receita de Venda | `3.01` Receitas da Intermediação Financeira | conceito de "receita" difere |
| Resultado bruto | `3.03` Resultado Bruto | `3.03` Result. Bruto Interm. Financeira | — |
| **EBIT** | `3.05` Result. Antes do Result. Financeiro e Tributos | ❌ não aplicável | banco: result. financeiro É o negócio |
| Result. antes dos tributos | `3.07` | `3.05` | **código diferente** |
| **Lucro líquido** | **`3.11`** Lucro/Prejuízo Consolidado | **`3.09`** Lucro/Prejuízo Consolidado | ⚠️ **código diferente — casar por DS_CONTA** |
| LPA reportado | `3.99` (pode vir 0 no pai) | `3.99` (ex.: 13,48) | preferir **calcular** LPA (ver §3) |

### 2.2 Balanço — Ativo (BPA — arquivo `..._BPA_con_...`)

| Indicador | 🏭 Industrial | 🏦 Banco |
|---|---|---|
| Ativo total | `1` Ativo Total | `1` Ativo Total |
| Ativo circulante | `1.01` Ativo Circulante | ❌ não existe (estrutura financeira: `1.02` Ativos Financeiros) |

> Banco **não tem** "Ativo Circulante/Não Circulante". Indicadores de liquidez corrente
> não se aplicam — tratar como N/A para 🏦.

### 2.3 Balanço — Passivo (BPP — arquivo `..._BPP_con_...`)

| Indicador | 🏭 Industrial | 🏦 Banco | Observação |
|---|---|---|---|
| Passivo total | `2` | `2` | — |
| **Patrimônio líquido** | **`2.03`** Patrimônio Líquido Consolidado | **`2.08`** Patrimônio Líquido Consolidado | ⚠️ **código diferente — casar por DS_CONTA** |
| Dívida (emprést. circ.) | `2.01.04` Empréstimos e Financiamentos | ❌ conceito difere | banco: `2.03` Passivos Financ. ao Custo Amortizado |
| Dívida (emprést. não circ.) | `2.02.01` Empréstimos e Financiamentos | ❌ | — |

### 2.4 Fluxo de Caixa (DFC método indireto — `..._DFC_MI_con_...`)

| Indicador | 🏭 Industrial | 🏦 Banco | Observação |
|---|---|---|---|
| **FCO** (caixa operacional) | `6.01` Caixa Líquido Atividades Operacionais | `6.01` (idem) | ✅ **consistente** nos dois |
| Caixa de investimento | `6.02` | `6.02` | usado em FCF |
| Depreciação & Amortização | sub-conta dentro de `6.01` | — | necessária p/ EBITDA (ver §4) |

---

## 3. Número de ações — LPA e VPA (arquivo `..._composicao_capital_...`)

Colunas (valores em **milhares de ações**):
`QT_ACAO_ORDIN_CAP_INTEGR`, `QT_ACAO_PREF_CAP_INTEGR`, `QT_ACAO_TOTAL_CAP_INTEGR`,
`QT_ACAO_ORDIN_TESOURO`, `QT_ACAO_PREF_TESOURO`, `QT_ACAO_TOTAL_TESOURO`.

- **Ações em circulação** = `QT_ACAO_TOTAL_CAP_INTEGR − QT_ACAO_TOTAL_TESOURO`.
- **LPA** = Lucro líquido ÷ ações em circulação.
- **VPA** = Patrimônio líquido ÷ ações em circulação.
- Verificado: VALE ≈ 4,539 mi ações; ITAÚ ≈ 9,804 mi (ON+PREF). Coerente com a realidade.

---

## 4. Política de tratamento por setor (decisão de produto)

O spike confirma que **alguns métodos não se aplicam a bancos**. Política proposta:

| Método (Camada 1) | 🏭 Industrial | 🏦 Banco |
|---|---|---|
| Buffett (ROE, margem, dívida/PL) | ✅ | ⚠️ ROE sim; dívida/PL e ROIC com ressalva |
| Graham (√22,5·LPA·VPA) | ✅ | ✅ (LPA/VPA existem) |
| DCF (FCO descontado) | ✅ | ❌ FCF de banco não é padrão → **excluir** |
| EV/EBITDA | ✅ | ❌ EBITDA não se aplica → **excluir** |
| Peter Lynch (PEG) | ✅ | ✅ |

> **Implicação para o score:** os pesos do score composto precisam ser **renormalizados**
> quando um método é N/A (não zerar — re-distribuir o peso entre os métodos válidos do setor).
> Isso vira um requisito da Camada 1 e deve aparecer no dashboard ("métodos aplicáveis").

---

## 5. EBITDA — nota de cálculo (industriais)

A CVM **não publica EBITDA pronto**. Cálculo padronizado:
`EBITDA = EBIT (DRE 3.05) + Depreciação + Amortização (DFC 6.01, sub-contas)`.
As sub-contas de D&A variam de nome entre empresas → exigem casamento por `DS_CONTA`
(contém "Deprecia"/"Amortiza"). Documentar a fórmula exata no código da Camada 1.

---

## 6. Itens em aberto (a fechar antes da Camada 1)

- [ ] Confirmar sub-contas exatas de **dívida** (`2.01.04` / `2.02.01`) em 2–3 industriais.
- [ ] Mapear sub-contas de **D&A** dentro do `6.01` para o EBITDA.
- [ ] Definir **classificação setorial** (financeiro vs operacional): usar setor da B3/brapi
      ou heurística pela estrutura da DRE (`3.01` "Intermediação Financeira" ⇒ banco).
- [ ] Repetir a verificação nos arquivos **ITR** (trimestral) — estrutura é a mesma, confirmar.
