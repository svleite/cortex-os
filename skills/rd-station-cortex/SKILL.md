---
name: rd-station-cortex
description: Consulta dados do RD Station Marketing via API v2 (token privado). Le leads por origem de ads (utm_source/medium/campaign), taxas de conversao por etapa do funil (lead → MQL → reuniao → proposta), eventos de conversao e calcula CPL qualificado real. Use quando o usuario mencionar rd station, rdstation, leads qualificados, funil de vendas, cpl qualificado, leads por origem, mql, reuniao agendada, proposta enviada, crm de leads, leads ads. Tambem dispara com /rd-station-cortex setup.
---

# RD Station Córtex

Skill para consulta de dados do RD Station Marketing via API v2 (token privado). Cruza leads de ads com estágios do funil para calcular CPL Qualificado real: não só CPL de clique, mas lead que chegou em reunião/oportunidade.

**IMPORTANTE: Esta skill é o braço de execução para RD Station. Para inteligência (diagnóstico, estratégia), use ads-cortex como camada acima.**

**IMPORTANTE: NUNCA usar MCPs de terceiros para RD Station. Esta skill usa SOMENTE os scripts Python locais.**

## Setup (primeira vez)

### 1. Verificar dependências

```bash
pip3 install requests python-dotenv pyyaml
```

### 2. Obter token privado

1. Acessar `app.rdstation.com.br/integracoes/tokens`
2. Aba **"Dados de Integração (API)"**
3. Copiar o **Token privado**
4. Preencher `RD_PRIVATE_TOKEN` em `~/.claude/skills/rd-station-cortex/.env`

### 3. Verificar acesso

```bash
python3 ~/.claude/skills/rd-station-cortex/scripts/read.py accounts
```

## Cadastro de clientes (contas.yaml)

**Arquivo:** `~/.claude/skills/rd-station-cortex/contas.yaml`

Antes de executar qualquer operação, o Claude DEVE ler este arquivo para resolver nomes de clientes para portal UUIDs.

Se o cliente não estiver cadastrado, perguntar os dados e oferecer para adicionar ao arquivo.

## Como usar

Todos os scripts estão em `~/.claude/skills/rd-station-cortex/scripts/`. O padrão é:

```
python3 <script>.py <subcomando> [argumentos]
```

O Claude deve interpretar o pedido do usuário e executar o script correto via Bash.

---

## Referência rápida de operações

### Leitura (read.py)

| Subcomando | O que faz | Exemplo |
|---|---|---|
| `auth` | Fluxo de autorização OAuth2 (primeira vez) | `read.py auth` |
| `accounts` | Lista portais RD Station acessíveis | `read.py accounts` |
| `leads` | Leads por origem UTM e período | `read.py leads --utm-source google` |
| `funnel` | Taxas de conversão por etapa do funil | `read.py funnel` |
| `conversions` | Eventos de conversão por data | `read.py conversions --since 2026-01-01 --until 2026-03-31` |
| `summary` | Visão geral: leads totais, taxas, CPL qualificado estimado | `read.py summary` |

### Parâmetros comuns

| Parâmetro | O que faz | Exemplo |
|---|---|---|
| `--cliente` | Nome do cliente (resolve via contas.yaml) | `--cliente Digitale` |
| `--utm-source` | Filtrar por origem (google, facebook, linkedin) | `--utm-source google,facebook` |
| `--utm-medium` | Filtrar por mídia | `--utm-medium cpc` |
| `--utm-campaign` | Filtrar por campanha | `--utm-campaign "camp-q1"` |
| `--since` | Data início (YYYY-MM-DD) | `--since 2026-01-01` |
| `--until` | Data fim (YYYY-MM-DD) | `--until 2026-03-31` |
| `--limit` | Limite de registros | `--limit 100` |

---

## Regras de segurança

1. **Somente leitura**: RD Station Córtex é skill de consulta, NÃO modifica dados
2. **Nunca hardcodar tokens**: sempre usar `.env` ou `contas.yaml`
3. **Respeitar rate limits**: se receber erro 429, aguardar 60s antes de tentar novamente
4. **Nunca assumir origem de dados**: ao mostrar métricas, SEMPRE especificar o período e o cliente consultado
5. **NUNCA usar MCPs**: esta skill usa SOMENTE os scripts Python locais

## Fluxos comuns

### CPL Qualificado (cruzamento ads × funil)

1. `read.py leads --utm-source google,facebook,linkedin --since 2026-01-01 --until 2026-03-31`: leads por canal
2. `read.py funnel`: taxa de conversão lead → reunião
3. `read.py summary`: CPL qualificado estimado por canal

### Diagnóstico de funil

1. `read.py funnel`: ver onde o funil quebra (taxa de MQL baixa? reunião? proposta?)
2. `read.py leads --utm-source google`: qualidade dos leads de cada canal

### Relatório mensal de leads

1. `read.py summary --since 2026-03-01 --until 2026-03-31`: visão geral
2. `read.py leads --since 2026-03-01 --until 2026-03-31`: detalhado por origem
