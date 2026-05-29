---
name: gtm-cortex
description: Gerencia containers Google Tag Manager via API REST oficial. Cria, lista, edita e publica tags, triggers, variáveis e versões. Autentica via OAuth user-flow. Use quando o usuário mencionar "GTM", "Google Tag Manager", "tag manager", "criar tag no GTM", "publicar container", "configurar pixel via GTM", "trigger no GTM", ou pedir alterações em containers GTM. Também dispara com /gtm-cortex setup.
---

# GTM Manager

Skill pra gerenciar Google Tag Manager via API REST. Substitui cliques manuais no painel do GTM por scripts versionados e replicáveis.

## Setup (primeira vez)

Autentica via **OAuth user-flow** (não service account). Motivo: o GTM rejeita service accounts criadas em projetos sem Workspace Identity (`Esse e-mail não corresponde a uma Conta do Google`). OAuth user-flow autentica como o próprio usuário — que já tem permissão nos containers — e funciona sempre.

**Passo 1 — Habilitar Tag Manager API no Google Cloud**
1. Abre `https://console.cloud.google.com/apis/library/tagmanager.googleapis.com`
2. Seleciona o projeto Google Cloud que usa pra suas integrações
3. Clica **Enable**

**Passo 2 — Configurar `.env` da skill**
Cria `.claude/skills/gtm-cortex/.env` com o template abaixo. `GTM_CLIENT_ID` e `GTM_CLIENT_SECRET` vêm do OAuth client que você criou no Google Cloud. O `GTM_REFRESH_TOKEN` é gerado no passo 3.

```
# GTM Manager - OAuth user-flow
# IMPORTANTE: este .env está no .gitignore. NUNCA commitar.

GTM_CLIENT_ID=""
GTM_CLIENT_SECRET=""
GTM_REFRESH_TOKEN=""
```

**Passo 3 — Rodar OAuth setup**
```bash
python3 .claude/skills/gtm-cortex/scripts/oauth_setup.py
```
- Vai abrir browser → loga com a conta Google que tem acesso ao GTM
- Aceita os escopos do Tag Manager
- Script salva o `refresh_token` no `.env` automaticamente

**Passo 4 — Validar**
```bash
python3 .claude/skills/gtm-cortex/scripts/auth.py
```
Deve listar accounts e containers acessíveis.

## Como usar

Scripts em `scripts/`:
- `auth.py` — testa autenticação, lista accounts/containers/workspaces
- `setup_pixel.py` — exemplo de script pra configurar Meta Pixel num container (adaptar pra cada projeto)

## Conceitos GTM

- **Account** → uma organização (ex: "Empresa X")
- **Container** → o `GTM-XXXX` que vai no site (1 por site/app)
- **Workspace** → branch de trabalho dentro do container (Default Workspace é o principal)
- **Tag** → o que dispara (ex: Meta Pixel, GA4, custom HTML)
- **Trigger** → quando dispara (page view, click, custom event)
- **Variable** → dado dinâmico (URL, click element, custom JS)
- **Version** → snapshot do container. Publicar = promover a versão pro container live

Tags só funcionam no site real depois de **publicar uma versão**.

## Segurança

- `.env` (com `GTM_REFRESH_TOKEN`) está no `.gitignore` — nunca commitar
- O refresh_token autentica como o usuário Google que rodou o `oauth_setup.py`. Tem acesso a tudo que aquele usuário acessa no GTM.
- Pra revogar: abre `https://myaccount.google.com/permissions` → encontra o OAuth client → Remove access. Isso invalida o refresh_token; rodar `oauth_setup.py` de novo pra gerar outro.
