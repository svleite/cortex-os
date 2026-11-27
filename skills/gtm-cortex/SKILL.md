---
name: gtm-cortex
description: Gerencia containers Google Tag Manager via API REST oficial. Cria, lista, edita e publica tags, triggers, variáveis e versões. Autentica via OAuth user-flow. Use quando o usuário mencionar "GTM", "Google Tag Manager", "tag manager", "criar tag no GTM", "publicar container", "configurar pixel via GTM", "trigger no GTM", ou pedir alterações em containers GTM. Também dispara com /gtm-cortex setup.
---

# GTM Manager

Skill para gerenciar Google Tag Manager via API REST. Substitui cliques manuais no painel do GTM por scripts versionados e replicáveis.

## Setup (primeira vez)

Autentica via **OAuth user-flow** (não service account). Motivo: o GTM rejeita service accounts criadas em projetos sem Workspace Identity (`Esse e-mail não corresponde a uma Conta do Google`). O OAuth user-flow autentica como o próprio usuário, que já tem permissão nos containers, e funciona sempre.

**Passo 1 — Habilitar Tag Manager API no Google Cloud**
1. Abra `https://console.cloud.google.com/apis/library/tagmanager.googleapis.com`
2. Selecione o projeto Google Cloud que você usa para suas integrações
3. Clique em **Enable**

**Passo 2 — Configurar `.env` da skill**
Crie `.claude/skills/gtm-cortex/.env` com o template abaixo. `GTM_CLIENT_ID` e `GTM_CLIENT_SECRET` vêm do OAuth client que você criou no Google Cloud. O `GTM_REFRESH_TOKEN` é gerado no passo 3.

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
- Abre o browser, então faça login com a conta Google que tem acesso ao GTM
- Aceite os escopos do Tag Manager
- O script salva o `refresh_token` no `.env` automaticamente

**Passo 4 — Validar**
```bash
python3 .claude/skills/gtm-cortex/scripts/auth.py
```
Deve listar accounts e containers acessíveis.

## Regra número 1: nada vai ao ar sem prévia e sem o usuário ver

1. Toda escrita (`receitas.py`, `publicar.py publicar|voltar`) **sem `--confirmar` só mostra o plano**. Mostre o plano, espere o ok explícito, rode de novo com `--confirmar`. Nunca use `--confirmar` sem aprovação na conversa.
2. Escrever no workspace **não muda o site**. O site só muda ao publicar uma versão.
3. A ordem não se pula: **receita (prévia) → `--confirmar` → modo Visualizar no GTM (o usuário testa) → `publicar.py publicar` (prévia, depois `--confirmar`) → `publicar.py verificar`**.
4. O container é sempre indicado pelo ID público (`--container GTM-XXXXXXX`), resolvido via API. Não gravar IDs de cliente em arquivo da skill.

## Como usar

Scripts em `scripts/` (só biblioteca padrão do Python 3.9+; saída em JSON):

- `auth.py`: testa autenticação, lista contas, containers e workspaces.
- `receitas.py`: monta configurações padrão num workspace. Idempotente: pula o que já existe **pelo nome ou pela função** (ex.: não cria um segundo vinculador de conversões se já houver um com outro nome) e avisa como se chama o equivalente.
- `publicar.py`: `status` (o que mudou no workspace), `publicar` (cria versão e publica), `voltar --versao N` (republica uma versão anterior), `verificar --site URL --procurar IDs` (baixa o `gtm.js` publicado e confere; sai com código 1 se faltar algo).
- `gtm_lib.py`: biblioteca comum (OAuth, chamadas, resolução de container).

### Receitas

| Receita | Parâmetros | O que monta |
|---|---|---|
| `base` | `--ga4 G-X` | Tag do Google do GA4 (inicialização) + vinculador de conversões |
| `google-ads` | `--ads AW-123` | Tag do Google da conta de anúncios + remarketing + vinculador |
| `lead-whatsapp` | `--ga4` e/ou `--ads-conversao AW-123/rotulo`; `--sem-joinchat`, `--sem-links` | Gatilho do evento `JoinChat` (plugin Joinchat do WordPress) + gatilho de clique em links `wa.me`/`api.whatsapp.com`/`whatsapp:`; evento GA4 `generate_lead` com `method=whatsapp`; conversão do Ads |
| `lead-telefone` | `--ga4` e/ou `--ads-conversao` | Gatilho de clique em `tel:` + `generate_lead` (`method=telefone`) + conversão |
| `meta-pixel` | `--pixel ID` `[--lead]` | Código base do pixel (PageView) + Lead no clique de WhatsApp (exige os gatilhos do `lead-whatsapp`) |

Exemplo completo:
```bash
S=~/.claude/skills/gtm-cortex/scripts
python3 $S/receitas.py listar        --container GTM-XXXXXXX
python3 $S/receitas.py lead-whatsapp --container GTM-XXXXXXX --ga4 G-XXXXXXX --ads-conversao AW-123456789/AbCdEf
#   ...mostrar o plano, ok do usuário...
python3 $S/receitas.py lead-whatsapp --container GTM-XXXXXXX --ga4 G-XXXXXXX --ads-conversao AW-123456789/AbCdEf --confirmar
#   ...usuário testa no modo Visualizar do GTM...
python3 $S/publicar.py publicar  --container GTM-XXXXXXX --nome "v4 - lead WhatsApp"          # prévia
python3 $S/publicar.py publicar  --container GTM-XXXXXXX --nome "v4 - lead WhatsApp" --confirmar
python3 $S/publicar.py verificar --container GTM-XXXXXXX --site https://cliente.com.br --procurar G-XXXXXXX,AW-123456789,JoinChat
```

Depois de publicar uma receita com `generate_lead`, marcar o evento como **principal** no GA4. Antes de mexer num container de cliente, ler `aprendizados.md`.

## Conceitos GTM

- **Account** → uma organização (ex: "Empresa X")
- **Container** → o `GTM-XXXX` que vai no site (1 por site/app)
- **Workspace** → branch de trabalho dentro do container (Default Workspace é o principal)
- **Tag** → o que dispara (ex: Meta Pixel, GA4, custom HTML)
- **Trigger** → quando dispara (page view, click, custom event)
- **Variable** → dado dinâmico (URL, click element, custom JS)
- **Version** → snapshot do container. Publicar = promover a versão para o container live

Tags só funcionam no site real depois de **publicar uma versão**.

## Segurança

- `.env` (com `GTM_REFRESH_TOKEN`) está no `.gitignore`, nunca commitar
- O refresh_token autentica como o usuário Google que rodou o `oauth_setup.py`. Tem acesso a tudo que aquele usuário acessa no GTM.
- Para revogar: abra `https://myaccount.google.com/permissions`, encontre o OAuth client e clique em Remove access. Isso invalida o refresh_token; rode `oauth_setup.py` de novo para gerar outro.
