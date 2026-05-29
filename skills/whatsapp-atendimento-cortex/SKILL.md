---
name: whatsapp-atendimento-cortex
description: Monta um bot de atendimento no WhatsApp via API oficial da Meta (Cloud API). Recebe mensagens 1:1 do cliente, responde com Claude usando a sua base de conhecimento, transcreve áudio e lê imagem, e faz handoff pra um humano quando detecta intenção de fechar (notifica o time com botão de "Assumir"). Roda em Cloudflare Worker + D1, sem servidor. Use quando o usuário disser "bot de WhatsApp", "atendimento automático no WhatsApp", "bot pra conversar com clientes", "WhatsApp Cloud API", "bot que responde no WhatsApp", "qualificar lead no WhatsApp", ou "/whatsapp-atendimento-cortex setup".
---

# WhatsApp Atendimento: Córtex

Bot de atendimento 1:1 no WhatsApp, na **API oficial da Meta** (Cloud API). O cliente manda mensagem, o bot responde com Claude com base na sua base de conhecimento, e quando a conversa esquenta (pedido de preço, intenção de fechar), passa pra um humano e avisa o time. Persiste tudo em D1.

## Entenda o terreno

- **Esta é a API OFICIAL.** Serve pra conversa 1:1 (empresa↔cliente). **Não lê grupos** (pra resumir grupo, use a skill `whatsapp-resumo-grupo-cortex`).
- O número vira **API-only**: ninguém usa o WhatsApp comum nele, tudo passa pelo Worker.
- **Custo:** responder dentro de 24h após o cliente escrever é **grátis**. Iniciar conversa fora disso exige template pago. Ver `references/custo-e-janela.md`.
- Sem servidor: roda em **Cloudflare Worker + D1 + Workers AI** (Whisper pra áudio) + **Claude** pra responder.

## Arquitetura

```
Meta Cloud API --webhook--> wa.SEUDOMINIO.com (Worker)
                               |
                               ├─ valida X-Hub-Signature-256 (HMAC)
                               ├─ grava em D1 (wa_conversas, wa_mensagens)
                               ├─ se status=bot: Claude responde (multimodal)
                               └─ se [HANDOFF]: marca 'humano' + avisa o time (botão Assumir / e-mail)
```

## Setup (primeira vez)

Guiar fase por fase. Cada fase termina com confirmação. Ler as `references/` conforme avança.

### Fase 1: Pré-condições

- [ ] **Business Manager** próprio (com a identidade/CNPJ do negócio, não de terceiro: BM com nome errado leva a ban).
- [ ] **Domínio no Cloudflare** (pra apontar `wa.seudominio.com` no webhook).
- [ ] **Chave da Anthropic API**.
- [ ] Decidir: começar no **número de teste** grátis da Meta (até 5 destinatários) antes do chip real.

### Fase 2: Meta

Seguir `references/setup-meta.md`: criar app + WABA + número de teste, pegar App Secret e token, e (ARMADILHA) inscrever a WABA no app via `subscribed_apps`.

### Fase 3: Cloudflare

Seguir `references/setup-cloudflare.md`: criar D1, aplicar `worker/db/schema.sql`, pôr os secrets, apontar o domínio do webhook, `npm run deploy`.

### Fase 4: Base de conhecimento

Editar `worker/src/kb.ts` (o `SYSTEM_PROMPT`): trocar os `<...>` pelo negócio, serviços, público e dores. **Manter a seção HANDOFF intacta** (é a mecânica que dispara o repasse pra humano).

### Fase 5: Webhook + teste

Configurar o webhook no painel da Meta (callback + verify token + assinar `messages`). Mandar mensagem do celular cadastrado e conferir a resposta + o D1.

## Operação

- **Comportamento do bot:** editar `worker/src/kb.ts` e `npm run deploy`.
- **Handoff:** o bot termina a resposta com `[HANDOFF]` (removido antes do envio), marca a conversa como `humano` e para de responder. O time recebe um botão "Assumir lead"; quem toca vira dono e recebe o histórico.
- **Notificação por e-mail:** opcional, via Resend (`NOTIFY_EMAIL_*`).
- **Multimodal:** áudio é transcrito (Whisper), imagem é lida pelo Claude.

## Arquivos

- `worker/src/index.ts`: webhook + persistência + envio + handoff
- `worker/src/kb.ts`: base de conhecimento (EDITAR aqui muda o bot)
- `worker/db/schema.sql`: esquema D1
- `worker/wrangler.toml`, `worker/.dev.vars.example`: config
- `references/`: setup Meta, setup Cloudflare, custo e janela de 24h

Ver também `aprendizados.md`.
