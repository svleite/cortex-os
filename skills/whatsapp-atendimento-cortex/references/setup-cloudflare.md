# Setup no Cloudflare (Worker + D1 + Workers AI)

O bot roda num Cloudflare Worker. Sem servidor: a Meta chama o webhook, o Worker responde.

## 1. Pré-requisitos

```bash
npx wrangler --version   # se faltar: npm install -g wrangler
npx wrangler login
```

## 2. Criar o D1 e aplicar o schema

```bash
cd worker
npm install
npx wrangler d1 create whatsapp-atendimento   # copie o database_id pro wrangler.toml
npx wrangler d1 execute whatsapp-atendimento --file=db/schema.sql --remote
```

Cole o `database_id` retornado em `wrangler.toml` (`[[d1_databases]]`).

## 3. Secrets

```bash
npx wrangler secret put WA_VERIFY_TOKEN     # string que você inventa (usa de novo no webhook)
npx wrangler secret put WA_APP_SECRET       # App Secret da Meta
npx wrangler secret put WA_TOKEN            # token (temp pra teste / System User pra prod)
npx wrangler secret put WA_PHONE_NUMBER_ID  # Phone Number ID
npx wrangler secret put ANTHROPIC_API_KEY   # chave Anthropic
npx wrangler secret put WA_NOTIFY_NUMBERS   # opcional: quem recebe o lead (vírgula-separado)
npx wrangler secret put WA_TEAM_NAMES       # opcional: "55...:Ana,55...:Bruno"
```

E-mail (opcional): `RESEND_API_KEY`, `NOTIFY_EMAIL_TO`, `NOTIFY_EMAIL_FROM`, `NOTIFY_EMAIL_CC`.

## 4. Domínio do webhook

O webhook precisa ser **público** (a Meta tem que alcançar). Em `wrangler.toml`, aponte um subdomínio próprio:

```toml
[[routes]]
pattern = "wa.SEUDOMINIO.com"
custom_domain = true
```

O domínio precisa estar no Cloudflare. Se usar Cloudflare Access em outros apps, **deixe `/webhook` fora do Access** (senão a Meta toma 403).

## 5. Deploy

```bash
npm run deploy
```

Depois volte ao painel da Meta e configure o webhook (ver `setup-meta.md` passo 3) + `subscribed_apps` (passo 2).

## 6. Testar

Mande mensagem do celular cadastrado pro número de teste. O bot deve responder. Confira o D1:

```bash
npx wrangler d1 execute whatsapp-atendimento --remote \
  --command="SELECT telefone,direcao,autor,texto FROM wa_mensagens ORDER BY id DESC LIMIT 10"
```

## Workers AI (transcrição de áudio)

O binding `[ai]` no `wrangler.toml` habilita o Whisper (`@cf/openai/whisper`) pra transcrever áudios recebidos. Tem free tier diário. Sem ele, áudio cai como "[áudio: não consegui transcrever]".
