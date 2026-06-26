# ADRs — Registro de Decisões de Arquitetura

> **O que é um ADR (Architecture Decision Record):** um registro curto de uma decisão
> importante — *contexto, decisão, consequências*. Serve para que, daqui a 6 meses, você
> (ou um avaliador) entenda **por que** o projeto é do jeito que é, sem reabrir a discussão.
> Cada decisão travada vira um ADR numerado e imutável (mudou? cria-se um novo que substitui).

---

## ADR-001 — Survivorship bias: documentar, não caçar preços de deslistadas

**Status:** Aceito · **Data:** 2026-06-25

### Contexto
A tese do projeto é "sem survivorship bias". A CVM mantém fundamentos de empresas
deslistadas, mas o spike confirmou que **fontes gratuitas (yfinance/brapi) não fornecem
histórico de preço confiável de ações deslistadas da B3**. O backtest precisa de preço.

### Decisão
Na v2, o universo usa ações **vivas**, e o survivorship bias do backtest é **medido e
documentado de forma explícita** (direção e magnitude estimada do viés), em vez de
resolvido com uma fonte frágil de preços de deslistadas.

### Consequências
- ➕ Automação estável (sem scraping frágil); honestidade que **aumenta** credibilidade.
- ➖ O retorno do backtest tende a ser **superestimado** — declarado abertamente no README.
- 🔭 Evolução futura: reconstruir preços de deslistadas (fica no item 16 do PRD).

### Importante
A **ferramenta viva (ranking diário)** NÃO sofre desse viés — ela ranqueia o que é
investível hoje. O viés afeta **apenas a prova histórica (backtest)**.

---

## ADR-002 — Universo do backtest por filtro de liquidez point-in-time

**Status:** Aceito · **Data:** 2026-06-25

### Contexto
A composição do IBrX-100 muda no tempo. Aplicar a composição **de hoje** ao passado
introduz **viés de seleção/look-ahead** (escolher no passado quem sabemos hoje que deu
certo). Obter a carteira teórica histórica oficial da B3 é trabalhoso e frágil para
automação.

### Decisão
- **Ferramenta viva:** universo = **IBrX-100 atual** (o que é investível hoje).
- **Backtest:** universo definido por uma **regra de liquidez point-in-time** — em cada
  data de rebalanceamento, selecionar ações acima de um limiar de volume/market cap,
  calculado **só com dados disponíveis naquela data**.

### Consequências
- ➕ Regra **reproduzível e auditável** (não uma lista baixada à mão); sem look-ahead de seleção.
- ➕ Mais defensável em entrevista do que "baixei a carteira do índice".
- ➖ Aproxima, mas não replica exatamente, a composição oficial do índice — declarado no README.

---

## ADR-003 — Documentação como resultado do spike (não como ponto de partida)

**Status:** Aceito · **Data:** 2026-06-25

### Contexto
Documentar antes de validar os dados arrisca registrar suposições que o spike prova
falsas (documentação de ficção).

### Decisão
Ordem de trabalho: **Spike de viabilidade → Documentação definitiva (dicionário de dados
+ ADRs) → Esqueleto do repo → Fatia vertical fina → Roadmap completo (Fases 1–6 do PRD).**

### Consequências
- ➕ Dicionário de dados nasce correto (ex.: já contempla plano de contas por setor).
- ➕ Menos retrabalho; cada etapa é pequena, revisável e didática.

---

## ADR-004 — Fontes de preço separadas por finalidade

**Status:** Aceito · **Data:** 2026-06-25 · **Origem:** achado do spike

### Contexto
O spike comprovou que cada fonte de preço serve melhor a um propósito: yfinance cobre
13 anos de histórico; brapi entrega o dado do dia sem token; histórico longo no brapi
exige token pago.

### Decisão
- **Histórico (backtest):** `yfinance` (com `curl_cffi` + cache + retries).
- **Corrente (ranking diário):** `brapi.dev`.

### Consequências
- ➕ Robustez e custo zero de API.
- ➖ Duas integrações de preço para manter; reconciliar diferenças de ajuste no Silver.
