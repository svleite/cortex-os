# Escolher o destino do resumo

A skill suporta 3 destinos, definidos por `DESTINO` no `.env`. O destino muda o que vai na coluna `target` de cada grupo.

## 1. `whatsapp_group` (mais simples)

Posta o resumo **de volta no próprio grupo**. Não precisa de mais nada (usa a mesma conexão do Evolution).

- `target`: ignorado.
- **Atenção:** todo mundo do grupo vê o resumo. Não serve se você quer acompanhar o grupo de forma discreta.

Cadastro:
```sql
INSERT INTO grp_config (group_jid, label, target) VALUES
 ('1203...@g.us', 'Equipe Comercial', NULL);
```

## 2. `discord_webhook` (discreto, sem bot)

Manda o resumo pra um canal do Discord via webhook. O grupo **não vê** nada. Não precisa de bot.

Criar o webhook: no Discord, canal → Editar Canal → Integrações → Webhooks → Novo Webhook → Copiar URL.

- `target`: a URL do webhook.

```sql
INSERT INTO grp_config (group_jid, label, target) VALUES
 ('1203...@g.us', 'Grupo Cliente X', 'https://discord.com/api/webhooks/...');
```

## 3. `discord_bot` (discreto, reusa um bot existente)

Igual ao webhook, mas posta via um bot do Discord (útil se você já tem um bot no servidor). Precisa de `DISCORD_BOT_TOKEN` no `.env` e do **channel ID** em `target`.

Listar os channel IDs:
```bash
DISCORD_BOT_TOKEN=xxx DISCORD_GUILD_ID=xxx node scripts/list-discord-channels.mjs
```

```sql
INSERT INTO grp_config (group_jid, label, target) VALUES
 ('1203...@g.us', 'Grupo Cliente X', '123456789012345678');
```

## Editar a config

```bash
# adicionar/editar: rode os INSERT/UPDATE via psql
docker compose exec postgres psql -U evolution -d evolution

# desativar um grupo sem apagar:
UPDATE grp_config SET enabled=false WHERE group_jid='...@g.us';
```
