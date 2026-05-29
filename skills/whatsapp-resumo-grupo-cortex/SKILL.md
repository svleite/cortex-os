---
name: whatsapp-resumo-grupo-cortex
description: Monta um bot que lê as mensagens das últimas 24h de grupos de WhatsApp, resume com Claude e entrega o resumo (no próprio grupo, no Discord ou em outro destino). Usa Evolution API (não-oficial, self-host) + Claude API + cron, tudo numa VPS. Use quando o usuário disser "resumo de grupo do WhatsApp", "bot que resume o grupo", "digest diário do WhatsApp", "ler mensagens de grupo com IA", "resumir conversas do WhatsApp", "monitorar grupo de cliente", ou "/whatsapp-resumo-grupo-cortex setup".
---

# WhatsApp Resumo de Grupo: Córtex

Bot que roda todo dia num horário fixo, puxa as mensagens das últimas 24h de um ou mais grupos de WhatsApp, manda pro Claude resumir e posta o resumo num destino (o próprio grupo, um canal do Discord, ou outro). Útil pra acompanhar grupos de clientes, comunidades ou equipes sem ler tudo.

## Entenda o terreno antes de montar

**A API oficial da Meta (WhatsApp Cloud API) NÃO lê grupos.** Ela serve só pra conversa 1:1 empresa↔cliente. Pra ler grupo, o único caminho é uma biblioteca/serviço **não-oficial** que fala o protocolo do WhatsApp Web. Esta skill usa **Evolution API** (open-source, self-host).

**Risco real:** soluções não-oficiais violam os Termos da Meta. O número usado **pode ser banido**. Regras de ouro:
- Use um **número dedicado e descartável** (chip pré-pago novo), NUNCA o número principal nem um WABA oficial.
- Quem entra no grupo precisa **consentir** (ou no mínimo você assumir o risco de relação).
- Não precisa criar conta em lugar nenhum: Evolution é self-host, a única chave é uma `EVOLUTION_API_KEY` que você inventa.

## Arquitetura (padrão PULL)

```
[cron diário na VPS]
   ↓
[Evolution API] → puxa as mensagens das 24h do grupo (PULL, /chat/findMessages)
   ↓
[Claude API] → gera o resumo no formato do prompt
   ↓
[Destino] → posta o resumo (grupo WhatsApp | Discord | etc.)
```

Tudo roda numa VPS (Evolution + Postgres + Redis + o app de resumo), num único `docker compose`. O Evolution já persiste as mensagens no Postgres dele; o app só puxa na hora do resumo (sem webhook, menos peça pra quebrar).

## Setup (primeira vez)

Guiar fase por fase. Cada fase termina com confirmação antes de seguir. Ler `references/` conforme necessário.

### Fase 1: Pré-condições (o gargalo costuma ser aqui, não no código)

Confirmar com o usuário, um a um:
- [ ] **Número dedicado**: chip pré-pago novo + um celular pra parear (scan de QR uma vez). Nunca o número pessoal/oficial.
- [ ] **VPS** always-on com Docker. Ver `references/setup-vps.md` (opções, custo, ARM grátis na Oracle).
- [ ] **Chave da Anthropic API** (Claude).
- [ ] **Destino definido**: postar de volta no grupo, ou mandar pro Discord (webhook), ou outro. Ver `references/setup-destino.md`.

Se faltar qualquer um, parar e resolver antes de codar.

### Fase 2: Subir o stack na VPS

Seguir `references/setup-evolution.md`. Resumo:
```bash
# na VPS, dentro da pasta da skill (app/):
cp .env.example .env      # preencher senhas, EVOLUTION_API_KEY, ANTHROPIC_API_KEY, DESTINO
docker compose up -d --build
docker compose logs -f evolution
```

### Fase 3: Parear o número

Evolution fica só no localhost. Abrir túnel SSH e escanear o QR com o WhatsApp do número dedicado. Comandos em `references/setup-evolution.md` (seção "parear").

### Fase 4: Mapear os grupos

Depois que o número entrar nos grupos, descobrir os JIDs:
```bash
curl http://127.0.0.1:8080/group/fetchAllGroups/<instancia>?getParticipants=false -H "apikey: <EVOLUTION_API_KEY>"
```
Cadastrar cada grupo na tabela `grp_config` (JID + label + destino). Ver `references/setup-destino.md` pro formato do destino.

### Fase 5: Testar

```bash
docker compose exec app sh -c 'wget -qO- --post-data="" http://localhost:3000/run-now'
```
Conferir o resumo no destino. Ajustar horário do cron (`SUMMARY_CRON`) e o prompt se quiser.

## Operação

- Cron diário no `.env` (`SUMMARY_CRON`, timezone fixado no app).
- Adicionar grupo: novo INSERT em `grp_config`. Desativar: `enabled=false`.
- Trocar modelo (Haiku ↔ Sonnet): `ANTHROPIC_MODEL` no `.env`.
- Logs: `docker compose logs -f app`.

## Arquivos

- `app/docker-compose.yml`: Evolution + Postgres + Redis + app
- `app/app/index.js`: PULL + resumo Claude + entrega (destino configurável)
- `app/scripts/list-discord-channels.mjs`: lista canais Discord (se o destino for Discord via bot)
- `references/`: tutoriais de VPS, Evolution e destino
- `contas.yaml.example`: modelo de config da conta

Ver também `aprendizados.md`.
