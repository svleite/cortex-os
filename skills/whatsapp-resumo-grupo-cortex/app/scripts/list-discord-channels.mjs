#!/usr/bin/env node
// Lista os canais de texto de um servidor Discord (útil quando DESTINO=discord_bot).
// Uso (token NUNCA no repo/chat; exporte na hora):
//   DISCORD_BOT_TOKEN=xxx DISCORD_GUILD_ID=xxx node scripts/list-discord-channels.mjs
// Opcional: DISCORD_CATEGORY_ID=xxx (filtra só uma categoria)

const TOKEN = process.env.DISCORD_BOT_TOKEN;
const GUILD = process.env.DISCORD_GUILD_ID;
const CATEGORY = process.env.DISCORD_CATEGORY_ID || null;

if (!TOKEN || !GUILD) {
  console.error("Faltou DISCORD_BOT_TOKEN ou DISCORD_GUILD_ID.");
  process.exit(1);
}

const resp = await fetch(`https://discord.com/api/v10/guilds/${GUILD}/channels`, {
  headers: { Authorization: `Bot ${TOKEN}` },
});
if (!resp.ok) {
  console.error(`Discord API ${resp.status}: ${await resp.text()}`);
  process.exit(1);
}

let channels = (await resp.json()).filter((c) => c.type === 0 || c.type === 5);
if (CATEGORY) channels = channels.filter((c) => c.parent_id === CATEGORY);
channels.sort((a, b) => (a.position ?? 0) - (b.position ?? 0));

console.log(`channel_id\tnome`);
for (const c of channels) console.log(`${c.id}\t${c.name}`);
console.log(`\nTotal: ${channels.length} canais.`);
