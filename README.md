# Garimpo Alpha B3

> ⚠️ **Disclaimer:** projeto educacional e de portfólio. **Não** constitui recomendação de
> investimento. Resultados passados não garantem resultados futuros.

**Otimizador de carteira de ações data-driven** para a B3 (universo IBrX-100). "Garimpa"
oportunidades combinando três camadas analíticas sobre uma arquitetura de dados moderna
(Medallion no Supabase):

1. **Fundamentalista** — 5 metodologias (Graham, Buffett, Lynch, EV/EBITDA, DCF) → score composto.
2. **Preditiva (ML)** — probabilidade calibrada de superar o Ibovespa (validação temporal + SHAP).
3. **Monte Carlo** — distribuição de valor justo e de risco/retorno da carteira (VaR/CVaR).

Projeto de portfólio que demonstra os papéis de **Engenheiro**, **Cientista** e **Analista de Dados**.

---

## Status

🟡 **Fase de fundação.** Documentação concluída; esqueleto do repositório montado.
Próximo: fatia vertical fina (1 ação fim-a-fim).

## Documentação

- [`PRD.md`](PRD.md) — especificação completa do produto.
- [`docs/01-spike-viabilidade.md`](docs/01-spike-viabilidade.md) — validação das fontes de dados.
- [`docs/02-decisoes-adr.md`](docs/02-decisoes-adr.md) — registro das decisões de arquitetura (ADRs).
- [`docs/03-dicionario-de-dados.md`](docs/03-dicionario-de-dados.md) — mapa CVM → indicadores (por setor).

## Stack

Python · Supabase (Postgres, Medallion) · SQLAlchemy · dbt · Pandera · scikit-learn /
XGBoost / LightGBM · SHAP · NumPy/SciPy · Prefect · Streamlit + Plotly · Docker · GitHub Actions.

---

## Como rodar (ambiente)

Pré-requisito: [`uv`](https://docs.astral.sh/uv/) instalado.

```bash
# 1. Criar o ambiente e instalar o núcleo de dependências
uv venv
uv sync

# 2. Configurar credenciais (copie o modelo e preencha com seu Supabase)
cp .env.example .env        # depois edite o .env com os valores reais

# 3. Rodar os testes
uv run pytest -q
```

Instale as dependências de cada fase só quando precisar:

```bash
uv sync --extra ingestion   # extratores (yfinance, brapi, BCB)
uv sync --extra ml          # modelagem
uv sync --extra dashboard   # Streamlit
```

> 🔒 **Segurança:** o arquivo `.env` (com senhas/chaves) **nunca** vai para o Git — está no
> `.gitignore`. Apenas o `.env.example` (modelo, sem segredos) é versionado.

## Estrutura

```
ingestion/     extratores multi-fonte -> Bronze
src/
  fundamental/ Camada 1 (scores)
  ml/          Camada 2 (modelo preditivo)
  montecarlo/  Camada 3 (simulação)
  config.py    configuração central (lê o .env)
dbt/           transformações Silver/Gold (SQL + testes)
data_quality/  validações Pandera
flows/         orquestração Prefect
dashboard/     app Streamlit
notebooks/     exploração narrada
tests/         testes automatizados
docs/          spike, ADRs, dicionário de dados
```
