# CLAUDE.md

Guia para o Claude Code trabalhar neste repositório. Veja `README.md` (estado atual) e
`PRD.md` (visão original + tabela de Fidelidade) para o panorama completo.

## O que é

**Garimpo Alpha B3** — pipeline de dados que ranqueia as ações do **IBrX-100** por fundamentos
(5 métodos), valuation (Monte Carlo/DCF) e risco, sobre uma arquitetura **Medallion** no
Supabase/PostgreSQL. Projeto educacional/portfólio. Python 3.11 + `uv`.

## Comandos

```bash
uv venv && uv sync --extra dev --extra ingestion --extra ml --extra dashboard  # ambiente
cp .env.example .env                                    # preencher SUPABASE_DB_URL

uv run python scripts/run_pipeline.py                   # pipeline fim-a-fim -> Supabase
uv run streamlit run dashboard/app.py                   # dashboard (http://localhost:8501)
uv run pytest -q                                        # testes (~41)
uv run ruff check .                                     # lint (CI exige limpo)
```

- **Scripts individuais precisam de `PYTHONPATH=.`** (ex.: `PYTHONPATH=. uv run python scripts/run_gold.py`). O `run_pipeline.py` já injeta isso nos subprocessos.
- **Ordem do pipeline:** Bronze CVM → Bronze preços → Silver → Gold → Monte Carlo → dataset ML.
- **Tabelas do Supabase usam `if_exists="replace"`** — cada execução reconstrói do zero.

## Arquitetura (Medallion no Supabase)

- **Bronze** (cru): `bronze_cvm_dre/bpp/bpa/dfc/acoes`, `bronze_prices`.
- **Silver** (`silver_fundamentals`): dedup do exercício, LPA/VPA, EBITDA, dívida líquida.
- **Gold**: `gold_fundamental_scores` (score+ranking+selos+`setor_economico`), `gold_montecarlo_*`,
  `meta_pipeline` (data da atualização, SELIC, nº de ações). `ml_dataset` alimenta ML/backtest.
- **Camadas analíticas** (`src/`): `fundamental/` (5 métodos + `score.py` z-score) · `ml/`
  (RF/XGB/LGBM, validação walk-forward) · `montecarlo/` (valuation + carteira).

## Convenções e armadilhas (não óbvias — leia antes de mexer)

- **Universo:** `src/universo.py` **carrega** `data/universo_ibrx100.csv` (não é dict fixo). Para
  atualizar: baixar a carteira IBrX-100 na B3 → `data/raw/b3/ibrx100.csv` → rodar
  `scripts/build_universo.py` (preserva CNPJs verificados, resolve setor pela CVM, marca
  `[CONFERIR]` ticker novo — **fuzzy match puro por nome é NÃO confiável**).
- **Dois campos de setor:** `setor` metodológico (`operacional`/`financeiro`) decide os métodos —
  financeiro recebe **3** (sem EV/EBITDA nem DCF), com pesos renormalizados. `setor_economico`
  (~11) é só vitrine/slicer. Podem discordar de propósito (BRAP4 = financeiro / Materiais Básicos).
- **Quirks da CVM** (tratados em `src/silver.py`):
  - Contas resolvidas por **descrição**, não por código (o código muda entre empresas).
  - `ESCALA_MOEDA`: algumas empresas reportam em **UNIDADE**, não MIL → `normalizar_escala` divide
    por 1000 (senão lucro/PL fica 1000× inflado).
  - Nº de ações **sem escala** → ancorado no `free_float` da carteira B3 (`acoes_em_circulacao`).
  - `composicao_capital` só existe **≥ 2020**; `DT_RECEB` é a âncora **point-in-time**.
- **Conexão:** `src/db.py` usa `SUPABASE_DB_URL` (lido por pydantic de env var **ou** `.env`);
  pooler porta 5432. Nunca versionar credenciais.
- **Survivorship bias:** documentado e **medido**, não resolvido (fontes gratuitas não têm preço
  de deslistadas) — ver ADR-001 e `scripts/analise_survivorship.py`.
- **Dashboards:** Streamlit (`dashboard/app.py`, protagonista) + Power BI (`garimpo-alpha-b3.pbix`).

## Escopo

Fora: execução de ordens, recomendação regulada, intraday/streaming, ações fora do IBrX-100,
autenticação. Roadmap (não implementado): dbt, Prefect, Pandera, Docker, SHAP.
