---
name: ga4-setup-cortex
description: Cria propriedades Google Analytics 4 e fluxos de dados web via Analytics Admin API. Gera Measurement ID (G-XXXXXXXXXX) e salva no arquivo do cliente. Use quando o usuário disser "criar GA4", "criar propriedade analytics", "criar property GA4", "configurar GA4", "setup GA4 para [cliente]", "preciso do Measurement ID", "criar analytics do cliente", ou "/ga4-setup-cortex". Contraparte de criação da skill ga4-reader (que é só leitura).
---

# GA4 Setup

Skill para criar propriedades Google Analytics 4 e web data streams via **Analytics Admin API**. Retorna o Measurement ID (`G-XXXXXXXXXX`) e opcionalmente atualiza um arquivo de configuração do cliente.

**Separado do ga4-reader** (leitura) e do gtm-cortex. O token OAuth do GTM não cobre escopos do Analytics Admin: essa skill tem seu próprio refresh token.

---

## Setup (primeira vez)

### 1. Habilitar Analytics Admin API no Google Cloud

1. Acesse `https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com`
2. Selecione o projeto Google Cloud que usa para suas integrações
3. Clique **Enable**

### 2. Configurar `.env`

Crie `.claude/skills/ga4-setup-cortex/.env` com o template abaixo. Se você já tem o `gtm-cortex` configurado, pode reusar o mesmo `CLIENT_ID` e `CLIENT_SECRET`, mas o `GA4C_REFRESH_TOKEN` precisa ser gerado separadamente (escopos diferentes).

```
# GA4 Setup - OAuth user-flow
# GA4C_REFRESH_TOKEN é DIFERENTE do GTM_REFRESH_TOKEN — escopos distintos.
# Gerar rodando: python3 scripts/oauth_setup.py
# IMPORTANTE: este .env está no .gitignore. NUNCA commitar.

GA4C_CLIENT_ID=""
GA4C_CLIENT_SECRET=""
GA4C_REFRESH_TOKEN=""
```

### 3. Rodar OAuth setup

```bash
python3 .claude/skills/ga4-setup-cortex/scripts/oauth_setup.py
```

- Abre browser → loga com a conta Google que tem acesso ao GA4
- Escopos: `analytics.edit` + `analytics.manage.users`
- **ATENÇÃO:** esses escopos são diferentes do GTM. Precisa gerar token novo mesmo que gtm-cortex já esteja configurado
- Script salva o `refresh_token` no `.env` automaticamente

### 4. Validar

```bash
python3 .claude/skills/ga4-setup-cortex/scripts/create_property.py accounts
```

Deve listar as contas GA4 acessíveis.

---

## Como usar

### Fluxo padrão para criar GA4 de um cliente

**Passo 1 — listar contas**

```bash
python3 .claude/skills/ga4-setup-cortex/scripts/create_property.py accounts
```

Anote o `account_id` da conta onde vai criar a propriedade.

**Passo 2 — criar propriedade + data stream**

```bash
python3 .claude/skills/ga4-setup-cortex/scripts/create_property.py create \
  --name "Nome do Cliente" \
  --url "https://www.seusite.com.br" \
  --timezone "America/Sao_Paulo" \
  --account-id "123456789" \
  --client-slug "slug-do-cliente"
```

O script:
1. Cria a propriedade GA4 na conta especificada
2. Cria o web data stream com a URL do site
3. Retorna o Measurement ID (`G-XXXXXXXXXX`)
4. Atualiza `clientes/[slug]/cliente.md` com o Measurement ID (se `--client-slug` for passado)

### Parâmetros de `create`

| Parâmetro | Obrigatório | Padrão | Descrição |
|---|---|---|---|
| `--name` | Sim | — | Nome da propriedade |
| `--url` | Sim | — | URL do site (ex: `https://www.seusite.com.br`) |
| `--account-id` | Sim | — | ID da conta GA4 (obter via `accounts`) |
| `--timezone` | Não | `America/Sao_Paulo` | Fuso horário |
| `--currency` | Não | `BRL` | Moeda |
| `--client-slug` | Não | — | Slug do cliente para atualizar `clientes/[slug]/cliente.md` |

---

## Conceitos GA4 Admin API

- **Account** → organização no GA4 (equivale ao "Analytics Account" no painel)
- **Property** → `properties/123456789` — a propriedade em si (antes chamada de "App + Web")
- **Data Stream** → fluxo de dados (web, iOS, Android). Web stream gera o `G-XXXXXXXXXX`
- **Measurement ID** → o `G-XXXXXXXXXX` que vai no GTM/snippet do site

Uma conta pode ter várias propriedades. Cada propriedade pode ter múltiplos data streams (ex: site + app). O Measurement ID é único por web stream.

---

## Segurança

- `.env` (com `GA4C_REFRESH_TOKEN`) está no `.gitignore` — nunca commitar
- O refresh_token autentica como o usuário Google que rodou `oauth_setup.py`
- Para revogar: `https://myaccount.google.com/permissions` → remove o OAuth client → rodar `oauth_setup.py` de novo

## Dependências

```bash
pip3 install google-analytics-admin google-auth google-auth-oauthlib
```
