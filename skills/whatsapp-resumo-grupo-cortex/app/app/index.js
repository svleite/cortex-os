import express from "express";
import cron from "node-cron";
import pg from "pg";
import Anthropic from "@anthropic-ai/sdk";

const { Pool } = pg;
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const MODEL = process.env.ANTHROPIC_MODEL || "claude-haiku-4-5";

const EVO_URL = process.env.EVOLUTION_URL;
const EVO_KEY = process.env.EVOLUTION_API_KEY;
const EVO_INSTANCE = process.env.EVOLUTION_INSTANCE || "default";

// DESTINO: whatsapp_group | discord_webhook | discord_bot
const DESTINO = process.env.DESTINO || "whatsapp_group";
const DISCORD_TOKEN = process.env.DISCORD_BOT_TOKEN; // só pra discord_bot
const TZ = process.env.TZ || "America/Sao_Paulo";

// grp_config.target:
//   whatsapp_group -> ignorado (posta no próprio grupo)
//   discord_webhook -> URL do webhook
//   discord_bot     -> channel ID
async function initDb() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS grp_config (
      group_jid TEXT PRIMARY KEY,
      label TEXT NOT NULL,
      target TEXT,
      enabled BOOLEAN DEFAULT true
    );
  `);
}

function extractText(message) {
  if (!message) return null;
  return (
    message.conversation ||
    message.extendedTextMessage?.text ||
    message.imageMessage?.caption ||
    message.videoMessage?.caption ||
    (message.audioMessage ? "[áudio]" : null) ||
    (message.documentMessage ? `[documento: ${message.documentMessage.fileName || ""}]` : null) ||
    (message.stickerMessage ? "[figurinha]" : null) ||
    null
  );
}

// ---- PULL: mensagens das últimas 24h direto do Evolution ----
async function fetchLast24h(groupJid) {
  const sinceMs = Date.now() - 24 * 60 * 60 * 1000;
  const resp = await fetch(`${EVO_URL}/chat/findMessages/${EVO_INSTANCE}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", apikey: EVO_KEY },
    body: JSON.stringify({ where: { key: { remoteJid: groupJid } }, limit: 2000 }),
  });
  if (!resp.ok) throw new Error(`Evolution findMessages ${resp.status}: ${await resp.text()}`);
  const json = await resp.json();
  const records = json?.messages?.records || json?.records || (Array.isArray(json) ? json : []);
  return records
    .map((m) => ({
      ts: Number(m.messageTimestamp) * 1000,
      push_name: m.pushName,
      body: extractText(m.message),
    }))
    .filter((m) => m.body && m.ts >= sinceMs)
    .sort((a, b) => a.ts - b.ts);
}

// ---- entrega ----
async function deliver(cfg, content) {
  if (DESTINO === "whatsapp_group") {
    const resp = await fetch(`${EVO_URL}/message/sendText/${EVO_INSTANCE}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: EVO_KEY },
      body: JSON.stringify({ number: cfg.group_jid, text: content }),
    });
    if (!resp.ok) throw new Error(`Evolution sendText ${resp.status}: ${await resp.text()}`);
  } else if (DESTINO === "discord_webhook") {
    for (let i = 0; i < content.length; i += 1900) {
      await fetch(cfg.target, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: content.slice(i, i + 1900) }),
      });
    }
  } else if (DESTINO === "discord_bot") {
    for (let i = 0; i < content.length; i += 1900) {
      const resp = await fetch(`https://discord.com/api/v10/channels/${cfg.target}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bot ${DISCORD_TOKEN}` },
        body: JSON.stringify({ content: content.slice(i, i + 1900) }),
      });
      if (!resp.ok) throw new Error(`Discord ${resp.status}: ${await resp.text()}`);
    }
  } else {
    throw new Error(`DESTINO desconhecido: ${DESTINO}`);
  }
}

async function summarizeGroup(cfg) {
  const msgs = await fetchLast24h(cfg.group_jid);
  if (msgs.length === 0) {
    console.log(`[${cfg.label}] sem mensagens em 24h, pulando`);
    return;
  }
  const transcript = msgs.map((m) => `${m.push_name || "?"}: ${m.body}`).join("\n");

  const prompt = `Abaixo, as mensagens das últimas 24h do grupo de WhatsApp "${cfg.label}".

Faça um resumo executivo do que foi tratado. Regras:
- Tom direto. Bullet points curtos.
- Destaque: decisões, pedidos, pendências, prazos, dúvidas, oportunidades.
- Se houver ação esperada de alguém, marque com "→ Ação:".
- Se foi conversa irrelevante (só "bom dia"/figurinha), diga em uma linha que não houve assunto material.

Mensagens (${msgs.length}):
${transcript}`;

  const resp = await anthropic.messages.create({
    model: MODEL,
    max_tokens: 1024,
    messages: [{ role: "user", content: prompt }],
  });
  const summary = resp.content.find((c) => c.type === "text")?.text || "(vazio)";
  const date = new Date().toLocaleDateString("pt-BR", { timeZone: TZ });
  const content = `📋 Resumo ${cfg.label} (${date}, ${msgs.length} mensagens)\n\n${summary}`;

  await deliver(cfg, content);
  console.log(`[${cfg.label}] resumo entregue via ${DESTINO} (${msgs.length} msgs)`);
}

async function runDailySummary() {
  console.log("== rodando resumo diário ==");
  const cfgs = await pool.query("SELECT * FROM grp_config WHERE enabled=true");
  for (const cfg of cfgs.rows) {
    try {
      await summarizeGroup(cfg);
    } catch (err) {
      console.error(`erro resumo ${cfg.label}`, err);
    }
  }
}

await initDb();
const CRON = process.env.SUMMARY_CRON || "0 18 * * *";
cron.schedule(CRON, runDailySummary, { timezone: TZ });

const app = express();
app.get("/health", (_req, res) => res.json({ ok: true, destino: DESTINO }));
app.post("/run-now", (_req, res) => {
  res.json({ started: true });
  runDailySummary();
});
app.listen(3000, () => console.log(`app on :3000, cron "${CRON}" (${TZ}), destino=${DESTINO}`));
