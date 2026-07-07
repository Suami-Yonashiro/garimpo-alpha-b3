# PRD — Garimpo Alpha B3.

**Produto:** Garimpo Alpha B3 · **Repositório:** `garimpo-alpha-b3`
**Versão:** 01 (consolidada) · **Status:** Aprovado para desenvolvimento · **Data:** 2026-06-25
**Autor:** Suami Yonashiro

> ⚠️ **Disclaimer:** projeto educacional e de portfólio. Não constitui recomendação de investimento. Resultados passados não garantem resultados futuros.

> 📌 **Este PRD é a VISÃO ORIGINAL** (jun/2026) e é mantido como registro da intenção de projeto. O que foi **de fato construído** diverge conscientemente em alguns pontos — a tabela abaixo documenta essa fidelidade para não gerar dúvida. O detalhamento do estado atual vive no [`README.md`](README.md) e nos [`docs/02-decisoes-adr.md`](docs/02-decisoes-adr.md).

### Fidelidade — visão original × o que foi construído

| Tema | Visão do PRD | Realidade construída |
|---|---|---|
| **Universo** | IBrX-100 | ✅ IBrX-100 (**99 ações**), da carteira B3 + cadastro CVM, versionado em `data/universo_ibrx100.csv` |
| **Setor** | categórico (1 feature) | ✅ **dois** campos: `setor` metodológico (`operacional`/`financeiro`) + `setor_economico` (~11, vitrine) |
| **Financeiras** | — | ✅ bancos/seguradoras/holdings recebem **3 métodos** (sem EV/EBITDA e DCF), pesos renormalizados |
| **Atualização** | diária (preços) + trimestral (CVM) | ⚠️ **manual** — um comando roda o pipeline; agendamento é roadmap |
| **ML — horizontes** | 4 (3/6/9/12m) + prob. calibrada + SHAP | ⚠️ **só 6m**, sem calibração/SHAP; AUC ~0,50 (honesto, sem vazamento) |
| **Orquestração** | Prefect | 📋 planejado (hoje: `run_pipeline.py` sequencial) |
| **Qualidade** | Pandera / dbt | 📋 planejado (hoje: ~41 testes pytest + ruff) |
| **Infra** | Docker | 📋 planejado |
| **Fonte `fundamentus`** | snapshot corrente | ❌ não usado (preço corrente vem do yfinance/brapi) |
| **Nomes de tabelas (§5)** | `raw_*`, `fact_*`, `dim_*` | nomes reais: `bronze_cvm_*`, `silver_fundamentals`, `gold_fundamental_scores`, `gold_montecarlo_*` |
| **Dashboard** | Streamlit | ✅ Streamlit + **Power BI** (showcase, `garimpo-alpha-b3.pbix`) |

> Legenda: ✅ conforme · ⚠️ parcial/diferente · 📋 planejado (roadmap) · ❌ descartado.
> As seções seguintes preservam o texto original da visão — cruze sempre com esta tabela.

---

## 1. Visão geral.
**Garimpo Alpha B3** é um **otimizador de carteira de ações data-driven** para o mercado brasileiro (B3). O produto "garimpa" oportunidades subvalorizadas no IBrX-100 combinando
três camadas analíticas sobre uma arquitetura de dados moderna (Medallion no Supabase):

1. **Camada Fundamentalista** — 5 metodologias consagradas (Graham, Buffett, Lynch, EV/EBITDA, DCF) consolidadas num **score composto** e ranking.
2. **Camada Preditiva (ML)** — modelos de árvore (Random Forest, XGBoost, LightGBM) estimando a **probabilidade de a ação superar o Ibovespa** em 3/6/9/12 meses.
3. **Camada de Simulação (Monte Carlo)** — distribuição probabilística de valor justo e de risco/retorno de carteira (2.500 simulações).

### Objetivo de portfólio.
Demonstrar, num único produto coeso e funcional, as competências dos três papéis:

| Papel | O que o projeto demonstra |
|---|---|
| **Engenheiro de Dados** | Arquitetura Bronze/Silver/Gold, ingestão multi-fonte, dado *point-in-time*, orquestração qualidade, Docker, CI/CD |
| **Cientista de Dados** | Feature engineering, modelagem supervisionada, validação temporal honesta, calibração de probabilidade, SHAP, simulação estocástica |
| **Analista de Dados** | Score interpretável, ranking, dashboard com storytelling e selos |

### Proposta de valor.
> Reduzir a análise de ~100 ações do IBrX-100 a um ranking acionável que combina **valor** (fundamentos), **probabilidade** (ML) e **risco** (Monte Carlo), com total transparência sobre como cada número é calculado.

---

## 2. Decisões travadas.
| # | Decisão | Valor |
|---|---|---|
| 1 | Universo de ações | **IBrX-100** (ações líquidas) |
| 2 | Horizonte do backtest | **Desde 2012** (~13 anos) |
| 3 | Nome / repositório | **Garimpo Alpha B3** / `garimpo-alpha-b3` |
| 4 | Atualização do pipeline | **Diária** (preços) + **trimestral** (fundamentos CVM) |
| 5 | Banco de dados | **Supabase (Postgres)** — Bronze/Silver/Gold |
| 6 | Normalização do score | **z-score global** + winsorização (1% / 99%) |
| 7 | DCF | Versão **padronizada e conservadora** (WACC ancorado na SELIC) |
| 8 | Target do ML | **Classificação binária** ("supera o Ibovespa? sim/não") |
| 9 | Validação do ML | **Temporal** (walk-forward / `TimeSeriesSplit`) — nunca k-fold aleatório |
| 10 | Dashboard | **Streamlit** (protagonista) · Power BI opcional |
| 11 | Natureza | Produto **greenfield** (não é continuação do smart-wallet-optimizer) |

---

## 3. Escopo.
### Dentro do escopo (v2).
- Ingestão multi-fonte (CVM, yfinance/brapi, fundamentus, BCB) → Bronze/Silver/Gold.
- Reconstrução de histórico **point-in-time** desde 2012 a partir da CVM.
- Camada fundamentalista (5 métodos + score composto + ranking).
- Camada preditiva (3 algoritmos, 4 horizontes, validação temporal, SHAP, backtest).
- Monte Carlo de valuation e de carteira (VaR/CVaR/drawdown).
- Dashboard Streamlit com storytelling e selos.
- Orquestração, qualidade de dados, Docker, CI.

### Fora do escopo (v2).
- Execução de ordens, corretagem ou robô de trade real.
- Recomendação financeira regulada (apenas disclaimer educacional).
- Dados intraday / streaming em tempo real.
- Ações fora da B3 / fora do IBrX-100.
- Autenticação de usuários / contas.

---

## 4. Fontes de dados.
| Fonte | Acesso | Conteúdo | Uso no projeto |
|---|---|---|---|
| **CVM — Dados Abertos** | CSV (dados.cvm.gov.br) | DFP (anual, desde 2010) e ITR (trimestral, desde 2011), com **data de divulgação** | Fundamentos *point-in-time* (treino do ML, séries históricas) |
| **yfinance / brapi.dev** | API | Preços OHLCV, cotações, dividendos | Preços diários, retornos, volatilidade, momentum |
| **fundamentus** | API/scraping | Snapshot atual de indicadores | Dados correntes para o ranking do dia |
| **BCB — SGS** | API (`python-bcb`) | Séries macro | Taxa de desconto (DCF) e features macro do ML |

### Séries macro do BCB (SGS).
| Série | Código | Uso |
|---|---|---|
| SELIC (meta) | 432 | Taxa livre de risco → WACC do DCF |
| CDI | 12 | Benchmark de renda fixa |
| IPCA | 433 | Retornos reais / ajuste de projeções |
| Câmbio USD/BRL | 1 | Feature macro (exportadoras/commodities) |

> **Por que CVM é a fonte-chave:** elimina os 3 vieses fatais do ML financeiro — (1) *point-in-time* real, (2) sem *look-ahead* (usa data de divulgação oficial), (3) sem *survivorship bias* (empresas que saíram da bolsa permanecem no histórico).

---

## 5. Arquitetura de dados (Medallion no Supabase).

> ℹ️ Diagrama da **visão original** (nomes de tabela `raw_*`/`fact_*` são aspiracionais — os nomes reais estão na tabela de **Fidelidade** no topo).

```text
Fontes: CVM · yfinance/brapi · fundamentus · BCB/SGS
   │ extração (Python, agendada)
   ▼
┌──────────────────── BRONZE ────────────────────┐  cru, append-only, com snapshot_date
│ raw_cvm_dfp, raw_cvm_itr, raw_prices,          │  preserva o ponto-no-tempo
│ raw_fundamentus, raw_bcb_macro                 │
└───────────────────────┬────────────────────────┘
   │ limpeza, tipagem, dedup, validação (Pandera)
   ▼
┌──────────────────── SILVER ────────────────────┐  1 linha por (ticker, data)
│ fact_fundamentals, fact_prices, dim_macro      │  indicadores derivados (LPA, VPA, EV…)
└───────────────────────┬────────────────────────┘
   │ regras de negócio + modelos
   ▼
┌───────────────────── GOLD ─────────────────────┐  pronto para consumo
│ fundamental_scores       (Camada 1)            │
│ ml_predictions           (Camada 2)            │
│ monte_carlo_valuation    (Camada 3 — #1)       │
│ monte_carlo_portfolio    (Camada 3 — #2)       │
│ stock_ranking            (visão final)         │
└───────────────────────┬────────────────────────┘
   ▼
Streamlit / Power BI
```

> **Trade-off documentado:** o purista guardaria o Bronze cru como arquivos (Parquet) em object storage. Para este produto, manter tudo no Supabase (Postgres) simplifica a stack e é totalmente adequado ao escopo. Supabase Storage fica como evolução futura para o raw.

---

## 6. Camada 1 — Análise Fundamentalista multi-metodologia.
Cada metodologia gera um **sub-score normalizado** via **z-score global** (com winsorização nos percentis 1% e 99% para conter outliers). O score final é uma média ponderada.

### Metodologias e pesos.
| Metodologia | Indicadores | Captura | Peso |
|---|---|---|---|
| **Buffett** | ROE, ROIC, Dívida/Patrimônio, Margem líquida | Qualidade e consistência do negócio | **30%** |
| **Graham** | Valor intrínseco `√(22.5·LPA·VPA)`, margem de segurança | Valor x preço | **20%** |
| **DCF** | Valor justo por fluxo de caixa descontado (padronizado) | Valor por geração de caixa | **20%** |
| **EV/EBITDA** | EV/EBITDA vs. setor | Valuation operacional | **15%** |
| **Peter Lynch** | PEG = (P/L)/crescimento, crescimento de lucros | Crescimento a preço razoável | **15%** |

> score_final = 0.30·s_buffett + 0.20·s_graham + 0.20·s_dcf + 0.15·s_evebitda + 0.15·s_lynch

- **Pesos configuráveis** (arquivo de config) e exibidos no dashboard.
- **DCF padronizado e conservador:** WACC ancorado na SELIC + prêmio de risco fixo por faixa; crescimento baseado no histórico de FCO; perpetuidade conservadora. Premissas transparentes.
- **Classificação:** Buy (margem > 25%), Hold (0–25%), Avoid (< 0%).
- **Saída (`fundamental_scores`):** ticker, sub-scores, score_final, classificação, percentil.

---

## 7. Camada 2 — Modelo Preditivo (ML).
### 7.1 Features.
P/L, P/VP, ROE, ROIC, Dívida/Patrimônio, crescimento de lucros, volatilidade, **margem líquida, liquidez, market cap, momentum de preço, setor (categórico)** e **macro (SELIC, IPCA, câmbio)**.

### 7.2 Target e modelagem.
- **Target:** classificação binária — *"a ação supera o Ibovespa no horizonte?"*
- **Horizontes:** 3 / 6 / 9 / 12 meses (4 modelos por algoritmo).
- **Algoritmos:** Random Forest, XGBoost, LightGBM — comparados lado a lado.
- **Validação:** **temporal obrigatória** (walk-forward / `TimeSeriesSplit`). Nunca k-fold aleatório (vaza o futuro). É o critério de qualidade nº 1 do projeto.
- **Saída:** **probabilidade calibrada** (ex.: "63% de chance de superar o índice") + **SHAP** para interpretabilidade.

### 7.3 Expectativa honesta de desempenho.
Prever retorno relativo ao índice é intrinsecamente difícil. Faixas realistas e honestas:
| Métrica | Faixa esperada (modelo bom e honesto) | 🚩 Alerta de vazamento |
|---|---|---|
| Acurácia | 54% – 60% | > 70% |
| AUC | 0.55 – 0.62 | > 0.75 |
> A **confiabilidade do produto não vem de acurácia mágica** — vem de: dado oficial point-in-time, validação temporal honesta, **backtest** vs. Ibovespa, gestão de risco (Monte Carlo) e transparência (SHAP + disclaimer). 

**Métrica de sucesso = performance no backtest e Sharpe**, não "% de acerto".

### 7.4 Backtest.
Estratégia: comprar as top-N ações do ranking e medir retorno vs. Ibovespa **desde 2012**, com validação temporal. Métricas: retorno acumulado, Sharpe, max drawdown, taxa de acerto.
**Saída (`ml_predictions`):** ticker, horizonte, probabilidade calibrada, principais SHAP.

---

## 8. Camada 3 — Simulação Monte Carlo (2.500 simulações).
### MC #1 — Probabilidade de subvalorização (sobre Graham/DCF).
Simular 2.500 cenários variando as premissas de valuation (LPA, crescimento, WACC/SELIC) → **distribuição do valor justo** → **probabilidade de o valor justo estar acima do preço atual**
(ex.: "78% de chance de a ação estar subvalorizada").
### MC #2 — Performance de carteira (top-N do ranking).
Simular 2.500 cenários de retorno conjunto com **matriz de correlação** entre os ativos → **distribuição de retorno da carteira**, **drawdown**, **VaR** e **CVaR**.
**Saídas:** `monte_carlo_valuation` (ticker, P5/P50/P95, prob_subvalorizada) e `monte_carlo_portfolio` (cenário, retorno, VaR, CVaR, drawdown).

---

## 9. Visão final integrada (Gold → consumo).
Ranking unificado por **selos** (mais interpretável e honesto que um único número):
| Selo | Critério |
|---|---|
| ✅ **Fundamentos fortes** | score_final no topo (ex.: percentil ≥ 70) |
| 📈 **ML favorável** | probabilidade de superar o índice acima do limiar |
| 🛡️ **Risco baixo** | VaR/CVaR e drawdown dentro do aceitável |
| 💎 **Subvalorizada** | Monte Carlo de valuation com alta prob. de preço justo > mercado | 

> **Saída (`stock_ranking`):** ticker, score, probabilidade, selos, classificação.

---

## 10. Stack tecnológica.

> ⚠️ **Stack planejada (visão).** dbt, Pandera, Prefect, Docker e SHAP **não** foram
> implementados — ver a tabela de **Fidelidade** no topo. O que roda hoje: Pandas/SQL,
> `run_pipeline.py` (orquestração sequencial), pytest + ruff, GitHub Actions (CI).

| Camada | Tecnologia |
|---|---|
| Extração | Python (requests, yfinance, `python-bcb`) |
| Armazenamento | **Supabase (Postgres)** + SQLAlchemy |
| Transformação | Pandas / SQL + **dbt** (modelos + testes) |
| Qualidade | **Pandera** (validação de schema/regras) |
| ML | scikit-learn, XGBoost, LightGBM, SHAP |
| Simulação | NumPy / SciPy |
| Orquestração | **Prefect** (DAGs, retries, agendamento) |
| Visualização | **Streamlit + Plotly** (Power BI opcional) |
| Infra | Docker · GitHub Actions (lint, testes, pipeline) |

---

## 11. Roadmap (ordem cronológica de trabalho).
Sequência por papel: **Engenharia de Dados → Cientista de Dados → Analista de Dados.**
| Fase | Bloco | Entrega |
|---|---|---|
| **1** | 🔧 Eng. de Dados | Ingestão multi-fonte (CVM, yfinance/brapi, fundamentus, BCB) → Bronze/Silver/Gold no Supabase; orquestração (Prefect); qualidade (Pandera); Docker; CI |
| **2** | 🔧 Eng. de Dados | Reconstrução do histórico **point-in-time** (CVM, desde 2012) — fundação do dataset de ML |
| **3** | 🔬 Cient. de Dados | Camada fundamentalista (5 métodos + z-score + ranking) |
| **4** | 🔬 Cient. de Dados | Modelo preditivo (RF/XGBoost/LightGBM, validação temporal, SHAP, probabilidade calibrada) + **backtest desde 2012** |
| **5** | 🔬 Cient. de Dados | Monte Carlo #1 (valuation) e #2 (carteira: VaR/CVaR/drawdown) |
| **6** | 📊 Analista de Dados | **Streamlit** sobre a Gold — storytelling, selos, dashboard (Power BI opcional) |

---

## 12. Design do dashboard (Streamlit).
**Estrutura (storytelling do macro ao específico):**
1. **Hero:** título + 4 KPIs grandes (nº de ações analisadas, nº de oportunidades "Buy", margem de segurança média, data da última atualização).
2. **Ranking principal:** tabela das top ações com os **selos** (✅ 📈 🛡️ 💎).
3. **Drill-down por ação:** radar dos 5 sub-scores; histograma do Monte Carlo de valor justo (com linha do preço atual); waterfall SHAP da previsão do ML.
4. **Carteira:** Monte Carlo da carteira top-N — distribuição de retorno, VaR/CVaR, drawdown.

**Estética:**
- **Visual contemporâneo e impactante** — referência de produto fintech moderno, que cause boa impressão logo no primeiro olhar.
- **Paleta que guia o olhar**: base neutra (dark mode) com 1–2 cores de destaque usadas de forma intencional para conduzir a atenção ao que importa (oportunidades, alertas, números-chave) — cor com função, não decoração.
- **Codificação por cor consistente**: verde = oportunidade/Buy, âmbar = neutro/Hold, vermelho = risco/Avoid — para o cérebro captar o dado antes de ler.
- **Diagramação equilibrada**: grid bem distribuído, hierarquia visual clara (número grande → contexto → detalhe), respiro/espaço em branco generoso, sem poluição.
- **Plotly em todos os gráficos** (interatividade, hover, zoom) com tema alinhado à paleta.
- **Tipografia limpa e moderna**, números em destaque.
- **Disclaimer** elegante e discreto no rodapé.

---

## 13. Riscos e mitigações.
| Risco | Mitigação |
|---|---|
| Histórico point-in-time | Fonte oficial CVM (data de divulgação) |
| Survivorship / look-ahead bias | CVM mantém empresas deslistadas; usar data de publicação |
| Data leakage temporal no ML | Validação walk-forward; nunca k-fold aleatório |
| Expectativa irreal de acurácia | Comunicar faixa honesta; sucesso medido por backtest/Sharpe |
| DCF subjetivo | Premissas padronizadas, conservadoras e transparentes |
| Rate limits / instabilidade de APIs | Retries, cache no Bronze, execução agendada |
| Responsabilidade (uso real) | Disclaimer educacional visível em todo o produto |

---

## 14. Métricas de sucesso (do projeto, não do investimento).
- Pipeline roda fim-a-fim, agendado, sem intervenção manual.
- Cobertura de qualidade (testes dbt/Pandera passando; validações de schema).
- ML com validação temporal honesta + interpretabilidade (SHAP) + backtest documentado.
- README com diagrama de arquitetura, dashboard clicável (link Streamlit) e limitações documentadas.
- Reprodutível: `docker compose up` sobe o ambiente.

---

## 15. Estrutura de pastas planejada.

> ℹ️ Estrutura **planejada** (visão). A estrutura **real** do repositório está no README (ex.: sem `flows/`, `dbt/`, `data_quality/` — ainda no roadmap).

```text
garimpo-alpha-b3/
├── README.md
├── PRD.md
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .github/workflows/ci.yml
├── flows/              # orquestração Prefect
├── ingestion/          # extratores: cvm, yfinance/brapi, fundamentus, bcb
├── dbt/                # modelos Silver/Gold + testes
├── src/
│   ├── fundamental/    # Graham, Buffett, Lynch, EV/EBITDA, DCF, score
│   ├── ml/             # features, treino, validação temporal, SHAP, backtest
│   └── montecarlo/     # valuation e portfólio
├── dashboard/          # app Streamlit
├── data_quality/       # validações Pandera
├── notebooks/          # exploração narrada
└── tests/
```

---

## 16. Itens em aberto para evolução (pós-v2).
- Otimização de carteira via fronteira eficiente (Markowitz / PyPortfolioOpt).
- Bronze cru em Supabase Storage (Parquet).
- Alertas/automação de atualização do ranking.
- Expansão do universo além do IBrX-100.