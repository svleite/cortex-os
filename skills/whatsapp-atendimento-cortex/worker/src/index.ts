/// <reference types="@cloudflare/workers-types" />

// Webhook da WhatsApp Cloud API (oficial da Meta) + bot de atendimento.
//   GET  /webhook  - verificação Meta (hub.challenge)
//   POST /webhook  - recebe `messages` + `phone_number_quality_update`
//
// Fluxo POST: valida assinatura > dedupe > grava entrada > (se status=bot) Claude > envia resposta.
// Handoff: o bot marca a conversa como 'humano' quando detecta intenção de fechar; aí para de responder
// e notifica o time (botão "Assumir" no WhatsApp + e-mail opcional).

import { SYSTEM_PROMPT } from "./kb";

interface Env {
  WA_DB: D1Database;
  AI: Ai;
  WA_VERIFY_TOKEN?: string;
  WA_APP_SECRET?: string;
  WA_TOKEN?: string;
  WA_PHONE_NUMBER_ID?: string;
  ANTHROPIC_API_KEY?: string;
  ANTHROPIC_MODEL?: string;
  BUSINESS_NAME?: string;        // nome do negócio, usado nas mensagens internas
  WA_NOTIFY_NUMBERS?: string;    // vírgula-separado, ex: "5519997656300,5519994981659"
  WA_TEAM_NAMES?: string;        // "5519997656300:Ana,5519994981659:Bruno" (mapa número->nome do time)
  WA_TEMPLATE_HANDOFF?: string;  // nome do template Utility de handoff (opcional)
  RESEND_API_KEY?: string;       // opcional: notificação por e-mail
  NOTIFY_EMAIL_FROM?: string;    // ex: bot@seudominio.com (precisa estar verificado no Resend)
  NOTIFY_EMAIL_TO?: string;
  NOTIFY_EMAIL_CC?: string;
}

const GRAPH = "https://graph.facebook.com/v22.0";

// Mapa número->nome do time (de WA_TEAM_NAMES). Cai pro próprio número se não mapeado.
function nomesTime(env: Env): Record<string, string> {
  const out: Record<string, string> = {};
  for (const par of (env.WA_TEAM_NAMES ?? "").split(",")) {
    const [num, nome] = par.split(":").map((s) => s.trim());
    if (num && nome) out[num] = nome;
  }
  return out;
}

// Número de notificação da plataforma Meta (onboarding/avisos). Não é lead.
const REMETENTES_META = new Set(["16465894168"]);

// Marcadores de texto das notificações da plataforma (defesa secundária, caso o número mude).
const MARCADORES_META =
  /(continue setting up your account|setup guidance|whatsapp manager|business\.facebook\.com\/latest\/whatsapp)/i;

function ehMensagemSistema(m: any): boolean {
  if (m?.type === "system") return true;
  if (REMETENTES_META.has(String(m?.from))) return true;
  const corpo = m?.text?.body ?? "";
  if (MARCADORES_META.test(corpo)) return true;
  return false;
}

// ---------- util ----------

// Recompõe o 9º dígito que o WhatsApp omite em celulares BR. Não-BR passa direto.
function normalizarTelefoneBR(raw: string): string {
  const d = raw.replace(/\D/g, "");
  if (!d.startsWith("55")) return d;
  const ddd = d.slice(2, 4);
  const resto = d.slice(4);
  if (resto.length === 8 && /^[6-9]/.test(resto)) return `55${ddd}9${resto}`;
  return d;
}

async function hmacHex(secret: string, msg: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(msg)));
  return [...sig].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function validarAssinatura(env: Env, req: Request, body: string): Promise<boolean> {
  if (!env.WA_APP_SECRET) return false;
  const header = req.headers.get("X-Hub-Signature-256");
  if (!header?.startsWith("sha256=")) return false;
  const esperado = await hmacHex(env.WA_APP_SECRET, body);
  return timingSafeEqual(header.slice(7), esperado);
}

// ---------- D1 ----------

async function jaProcessada(env: Env, waId: string): Promise<boolean> {
  const r = await env.WA_DB.prepare("SELECT 1 FROM wa_mensagens WHERE wa_id=?").bind(waId).first();
  return !!r;
}

async function gravarEntrada(
  env: Env,
  tel: string,
  nome: string | null,
  msg: { id: string; tipo: string; texto: string },
  raw: unknown,
  origem: string,
): Promise<void> {
  const janela = new Date(Date.now() + 24 * 3600 * 1000).toISOString();
  await env.WA_DB.batch([
    env.WA_DB.prepare(
      `INSERT INTO wa_conversas (telefone,nome,origem,ultima_msg,janela_ate)
       VALUES (?1,?2,?3,?4,?5)
       ON CONFLICT(telefone) DO UPDATE SET
         nome=COALESCE(excluded.nome,wa_conversas.nome),
         ultimo_em=datetime('now'), ultima_msg=excluded.ultima_msg, janela_ate=excluded.janela_ate`,
    ).bind(tel, nome, origem, msg.texto.slice(0, 200), janela),
    env.WA_DB.prepare(
      `INSERT OR IGNORE INTO wa_mensagens (wa_id,telefone,direcao,autor,tipo,texto,raw)
       VALUES (?1,?2,'in','cliente',?3,?4,?5)`,
    ).bind(msg.id, tel, msg.tipo, msg.texto, JSON.stringify(raw)),
  ]);
}

async function gravarSaida(env: Env, tel: string, texto: string, waId: string | null, autor: string): Promise<void> {
  await env.WA_DB.batch([
    env.WA_DB.prepare(
      `INSERT OR IGNORE INTO wa_mensagens (wa_id,telefone,direcao,autor,tipo,texto)
       VALUES (?1,?2,'out',?3,'text',?4)`,
    ).bind(waId ?? `out-${crypto.randomUUID()}`, tel, autor, texto),
    env.WA_DB.prepare(
      `UPDATE wa_conversas SET ultimo_em=datetime('now'), ultima_msg=? WHERE telefone=?`,
    ).bind(texto.slice(0, 200), tel),
  ]);
}

async function statusConversa(env: Env, tel: string): Promise<string> {
  const r = await env.WA_DB.prepare("SELECT status FROM wa_conversas WHERE telefone=?").bind(tel).first<{ status: string }>();
  return r?.status ?? "bot";
}

async function marcarHumano(env: Env, tel: string): Promise<void> {
  await env.WA_DB.prepare("UPDATE wa_conversas SET status='humano' WHERE telefone=?").bind(tel).run();
}

// Horário comercial (BRT = UTC-3): seg-sex, 9h-18h. Ajuste se precisar.
function isHorarioComercial(): boolean {
  const brt = new Date(Date.now() - 3 * 60 * 60 * 1000);
  const dia = brt.getUTCDay();
  const hora = brt.getUTCHours();
  return dia >= 1 && dia <= 5 && hora >= 9 && hora < 18;
}

function despedidaHandoff(env: Env): string {
  const nome = env.BUSINESS_NAME ?? "nosso time";
  if (isHorarioComercial()) {
    return `Entendido! Já avisei a equipe ${nome}. Em instantes alguém entra em contato com você por aqui.`;
  }
  return "Nosso atendimento funciona de segunda a sexta, das 9h às 18h (horário de Brasília). Já registrei seu contato e avisei a equipe: se houver alguém disponível agora, você será contatado em breve. Caso contrário, retornamos na primeira hora útil.";
}

async function marcarAssumido(env: Env, tel: string, por: string): Promise<void> {
  await env.WA_DB.prepare("UPDATE wa_conversas SET assumido_por=? WHERE telefone=?").bind(por, tel).run();
}

async function historico(env: Env, tel: string): Promise<AnthropicMsg[]> {
  const { results } = await env.WA_DB.prepare(
    `SELECT direcao,texto FROM wa_mensagens WHERE telefone=? AND texto IS NOT NULL AND texto<>''
     ORDER BY criado_em DESC LIMIT 12`,
  ).bind(tel).all<{ direcao: string; texto: string }>();
  return (results ?? [])
    .reverse()
    .map((m) => ({ role: m.direcao === "in" ? "user" : "assistant", content: m.texto }) as AnthropicMsg);
}

// ---------- Media download ----------

async function baixarMedia(env: Env, mediaId: string): Promise<{ bytes: Uint8Array; mime: string } | null> {
  if (!env.WA_TOKEN) return null;
  try {
    const meta = await fetch(`${GRAPH}/${mediaId}`, { headers: { authorization: `Bearer ${env.WA_TOKEN}` } });
    if (!meta.ok) {
      console.error("baixarMedia: meta erro", meta.status, await meta.text());
      return null;
    }
    const { url, mime_type } = (await meta.json()) as { url?: string; mime_type?: string };
    if (!url) return null;
    const bin = await fetch(url, { headers: { authorization: `Bearer ${env.WA_TOKEN}` } });
    if (!bin.ok) {
      console.error("baixarMedia: bin erro", bin.status);
      return null;
    }
    return { bytes: new Uint8Array(await bin.arrayBuffer()), mime: mime_type ?? "application/octet-stream" };
  } catch (e) {
    console.error("baixarMedia: exception", e);
    return null;
  }
}

function bytesParaBase64(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin);
}

// ---------- ASR (Workers AI Whisper) ----------

async function transcreverAudio(env: Env, mediaId: string): Promise<string | null> {
  const m = await baixarMedia(env, mediaId);
  if (!m) return null;
  try {
    const out = (await env.AI.run("@cf/openai/whisper", { audio: [...m.bytes] })) as { text?: string };
    return out.text?.trim() || null;
  } catch (e) {
    console.error("whisper erro", e);
    return null;
  }
}

// ---------- Anthropic ----------

type AnthropicMsg = {
  role: "user" | "assistant";
  content: string | Array<
    | { type: "text"; text: string }
    | { type: "image"; source: { type: "base64"; media_type: string; data: string } }
  >;
};

async function pensar(env: Env, mensagens: AnthropicMsg[]): Promise<string> {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": env.ANTHROPIC_API_KEY!,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: env.ANTHROPIC_MODEL || "claude-haiku-4-5",
      max_tokens: 500,
      system: SYSTEM_PROMPT,
      messages: mensagens,
    }),
  });
  if (!res.ok) {
    console.error("anthropic erro", res.status, await res.text());
    return "Recebi sua mensagem. Já te respondo.";
  }
  const data = (await res.json()) as { content?: { type: string; text?: string }[] };
  return data.content?.filter((b) => b.type === "text").map((b) => b.text).join("\n").trim() || "...";
}

// ---------- envio Graph API ----------

async function enviarTexto(env: Env, para: string, texto: string): Promise<string | null> {
  if (!env.WA_TOKEN || !env.WA_PHONE_NUMBER_ID) {
    console.error("sem WA_TOKEN/WA_PHONE_NUMBER_ID");
    return null;
  }
  const res = await fetch(`${GRAPH}/${env.WA_PHONE_NUMBER_ID}/messages`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${env.WA_TOKEN}` },
    body: JSON.stringify({
      messaging_product: "whatsapp",
      to: para,
      type: "text",
      text: { body: texto.slice(0, 4000) },
    }),
  });
  if (!res.ok) {
    console.error("envio erro", res.status, await res.text());
    return null;
  }
  const data = (await res.json()) as { messages?: { id: string }[] };
  return data.messages?.[0]?.id ?? null;
}

async function enviarTemplate(env: Env, para: string, nome: string): Promise<string | null> {
  if (!env.WA_TOKEN || !env.WA_PHONE_NUMBER_ID) return null;
  const res = await fetch(`${GRAPH}/${env.WA_PHONE_NUMBER_ID}/messages`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${env.WA_TOKEN}` },
    body: JSON.stringify({
      messaging_product: "whatsapp",
      to: para,
      type: "template",
      template: { name: nome, language: { code: "pt_BR" } },
    }),
  });
  if (!res.ok) {
    console.error("envio template erro", res.status, await res.text());
    return null;
  }
  const data = (await res.json()) as { messages?: { id: string }[] };
  return data.messages?.[0]?.id ?? null;
}

async function enviarBotaoAssumir(env: Env, para: string, telLead: string, nomeLead: string | null): Promise<void> {
  if (!env.WA_TOKEN || !env.WA_PHONE_NUMBER_ID) return;
  const negocio = env.BUSINESS_NAME ?? "Atendimento";
  const corpo = `🔔 *Lead quente (${negocio})*\nDe: ${nomeLead ?? "?"} (${telLead})\nO bot passou pra humano. Toque pra assumir.`;
  const res = await fetch(`${GRAPH}/${env.WA_PHONE_NUMBER_ID}/messages`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${env.WA_TOKEN}` },
    body: JSON.stringify({
      messaging_product: "whatsapp",
      to: para,
      type: "interactive",
      interactive: {
        type: "button",
        body: { text: corpo },
        action: { buttons: [{ type: "reply", reply: { id: `assumi_${telLead}`, title: "✅ Assumir lead" } }] },
      },
    }),
  });
  if (!res.ok) console.error("envio botao erro", res.status, await res.text());
}

async function processarComandoTime(env: Env, remetente: string, m: any): Promise<void> {
  let telLead: string | null = null;
  const texto: string = m.type === "text" ? (m.text?.body ?? "") : "";
  if (m.type === "interactive" && m.interactive?.button_reply?.id?.startsWith("assumi_")) {
    telLead = m.interactive.button_reply.id.replace("assumi_", "");
  } else {
    const match = texto.trim().match(/^ASSUMI\s+(\d+)$/i);
    if (match) telLead = normalizarTelefoneBR(match[1]);
  }
  if (!telLead) return;

  const lead = await env.WA_DB.prepare(
    "SELECT nome, assumido_por FROM wa_conversas WHERE telefone=?",
  ).bind(telLead).first<{ nome: string | null; assumido_por: string | null }>();

  if (!lead) {
    await enviarTexto(env, remetente, `⚠️ Conversa ${telLead} não encontrada.`);
    return;
  }
  if (lead.assumido_por) {
    await enviarTexto(env, remetente, `ℹ️ Esse lead já foi assumido por ${lead.assumido_por}.`);
    return;
  }

  const nomeAtendente = nomesTime(env)[remetente] ?? remetente;
  await marcarAssumido(env, telLead, nomeAtendente);
  await enviarTexto(env, remetente, `✅ Lead ${lead.nome ?? telLead} marcado como seu.\nFalar agora: https://wa.me/${telLead}`);

  const msgs = await env.WA_DB.prepare(
    `SELECT direcao, texto FROM wa_mensagens WHERE telefone=? AND texto IS NOT NULL AND texto<>''
     ORDER BY criado_em ASC LIMIT 20`,
  ).bind(telLead).all<{ direcao: string; texto: string }>();
  if (msgs.results && msgs.results.length > 0) {
    const linhas = msgs.results.map((mm) => `${mm.direcao === "in" ? "👤" : "🤖"} ${mm.texto}`);
    const hist = `📋 Histórico (${lead.nome ?? telLead})\n${"─".repeat(30)}\n${linhas.join("\n\n")}`;
    await enviarTexto(env, remetente, hist.slice(0, 4000));
  }

  const outros = (env.WA_NOTIFY_NUMBERS ?? "").split(",").map((n) => n.trim()).filter((n) => n && n !== remetente);
  if (outros.length > 0) {
    const aviso = `✅ ${nomeAtendente} assumiu o lead ${lead.nome ?? "?"} (${telLead}). Pode ignorar.`;
    await Promise.all(outros.map((n) => enviarTexto(env, n, aviso)));
  }
}

// ---------- processamento (em background, depois do 200) ----------

async function processarMensagem(env: Env, value: any): Promise<void> {
  const msgs = value?.messages;
  if (!Array.isArray(msgs) || msgs.length === 0) return;
  const contatoNome = value?.contacts?.[0]?.profile?.name ?? null;

  for (const m of msgs) {
    if (ehMensagemSistema(m)) {
      await env.WA_DB.prepare("INSERT INTO wa_eventos (tipo,detalhe,raw) VALUES ('sistema',?,?)")
        .bind(String(m?.from ?? ""), JSON.stringify(m)).run();
      continue;
    }

    const tel = normalizarTelefoneBR(m.from);
    const waId: string = m.id;
    if (await jaProcessada(env, waId)) continue;

    const numerosTime = (env.WA_NOTIFY_NUMBERS ?? "").split(",").map((n) => n.trim()).filter(Boolean);
    if (numerosTime.includes(tel)) {
      await processarComandoTime(env, tel, m);
      continue;
    }

    let texto = "";
    let imagemBase64: { mime: string; data: string } | null = null;
    if (m.type === "text") texto = m.text?.body ?? "";
    else if (m.type === "interactive") texto = m.interactive?.button_reply?.title ?? m.interactive?.list_reply?.title ?? "";
    else if (m.type === "button") texto = m.button?.text ?? "";
    else if (m.type === "audio" && m.audio?.id) {
      const t = await transcreverAudio(env, m.audio.id);
      texto = t ? `[áudio transcrito] ${t}` : "[áudio: não consegui transcrever]";
    } else if (m.type === "image" && m.image?.id) {
      const media = await baixarMedia(env, m.image.id);
      if (media) {
        imagemBase64 = { mime: media.mime, data: bytesParaBase64(media.bytes) };
        const cap = m.image.caption?.trim();
        texto = cap ? `[imagem] ${cap}` : "[imagem]";
      } else texto = "[imagem: não consegui baixar]";
    } else texto = `[${m.type}]`;

    const origem = m.referral ? "ctwa" : "organico"; // referral = veio de Click-to-WhatsApp
    await gravarEntrada(env, tel, contatoNome, { id: waId, tipo: m.type, texto }, m, origem);

    if ((await statusConversa(env, tel)) !== "bot") continue;
    if (!env.ANTHROPIC_API_KEY) continue;

    const hist = await historico(env, tel);
    if (imagemBase64 && hist.length > 0 && hist[hist.length - 1].role === "user") {
      const ultima = hist[hist.length - 1];
      const textoUltima = typeof ultima.content === "string" ? ultima.content : "";
      hist[hist.length - 1] = {
        role: "user",
        content: [
          { type: "image", source: { type: "base64", media_type: imagemBase64.mime, data: imagemBase64.data } },
          { type: "text", text: textoUltima || "Analise a imagem." },
        ],
      };
    }
    const resposta = await pensar(env, hist);
    const handoff = /\[HANDOFF\]/i.test(resposta);

    if (handoff) {
      let enviado: string | null = null;
      if (isHorarioComercial() && env.WA_TEMPLATE_HANDOFF) {
        enviado = await enviarTemplate(env, tel, env.WA_TEMPLATE_HANDOFF);
        if (enviado) await gravarSaida(env, tel, `[template:${env.WA_TEMPLATE_HANDOFF}]`, enviado, "bot");
      }
      if (!enviado) {
        const msg = despedidaHandoff(env);
        enviado = await enviarTexto(env, tel, msg);
        await gravarSaida(env, tel, msg, enviado, "bot");
      }
      await marcarHumano(env, tel);
      await notificarTime(env, tel, contatoNome);
    } else {
      const limpa = resposta.replace(/\[HANDOFF\]/gi, "").trim();
      const enviado = await enviarTexto(env, tel, limpa);
      await gravarSaida(env, tel, limpa, enviado, "bot");
    }
  }
}

async function notificarTime(env: Env, tel: string, nome: string | null): Promise<void> {
  const hist = await historico(env, tel);
  await Promise.all([
    env.WA_NOTIFY_NUMBERS
      ? (async () => {
          const numeros = env.WA_NOTIFY_NUMBERS!.split(",").map((n) => n.trim()).filter(Boolean);
          await Promise.all(numeros.map((n) => enviarBotaoAssumir(env, n, tel, nome)));
        })()
      : Promise.resolve(),
    env.RESEND_API_KEY && env.NOTIFY_EMAIL_TO && env.NOTIFY_EMAIL_FROM
      ? enviarEmailHandoff(env, tel, nome, hist)
      : Promise.resolve(),
  ]);
}

async function enviarEmailHandoff(
  env: Env,
  tel: string,
  nome: string | null,
  hist: { role: string; content: string | unknown }[],
): Promise<void> {
  const linhas = hist
    .map((m) => {
      const c = typeof m.content === "string" ? m.content : "[mídia]";
      return `<tr style="vertical-align:top"><td style="padding:4px 8px;color:#888;white-space:nowrap">${m.role === "user" ? "Lead" : "Bot"}</td><td style="padding:4px 8px">${c.replace(/</g, "&lt;").replace(/\n/g, "<br>")}</td></tr>`;
    })
    .join("");

  const html = `<p><strong>Lead:</strong> ${nome ?? "?"} (<strong>Tel:</strong> ${tel})</p>
<table style="border-collapse:collapse;font-family:sans-serif;font-size:14px;width:100%">
  <thead><tr style="background:#f4f4f4"><th style="padding:4px 8px;text-align:left">De</th><th style="padding:4px 8px;text-align:left">Mensagem</th></tr></thead>
  <tbody>${linhas}</tbody>
</table>`;

  const cc = env.NOTIFY_EMAIL_CC ? [{ email: env.NOTIFY_EMAIL_CC }] : [];
  const negocio = env.BUSINESS_NAME ?? "WhatsApp Bot";
  await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${env.RESEND_API_KEY}` },
    body: JSON.stringify({
      from: `${negocio} <${env.NOTIFY_EMAIL_FROM}>`,
      to: [env.NOTIFY_EMAIL_TO],
      cc,
      subject: `Lead WhatsApp: ${nome ?? "?"} (${tel})`,
      html,
    }),
  }).then((r) => { if (!r.ok) r.text().then((t) => console.error("resend erro", r.status, t)); });
}

async function processarStatus(env: Env, value: any): Promise<void> {
  if (Array.isArray(value?.statuses)) {
    for (const s of value.statuses) {
      await env.WA_DB.prepare("INSERT INTO wa_eventos (tipo,detalhe,raw) VALUES ('status',?,?)")
        .bind(`${s.status} ${s.recipient_id ?? ""}`.trim(), JSON.stringify(s)).run();
    }
  }
}

// ---------- handler ----------

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname !== "/webhook") return new Response("ok", { status: 200 });

    if (req.method === "GET") {
      const mode = url.searchParams.get("hub.mode");
      const token = url.searchParams.get("hub.verify_token");
      const challenge = url.searchParams.get("hub.challenge");
      if (mode === "subscribe" && env.WA_VERIFY_TOKEN && token === env.WA_VERIFY_TOKEN && challenge) {
        return new Response(challenge, { status: 200, headers: { "content-type": "text/plain" } });
      }
      return new Response("forbidden", { status: 403 });
    }

    if (req.method !== "POST") return new Response("method not allowed", { status: 405 });

    const body = await req.text();
    if (!(await validarAssinatura(env, req, body))) {
      return new Response("invalid signature", { status: 401 });
    }

    let payload: any;
    try {
      payload = JSON.parse(body);
    } catch {
      return new Response("bad json", { status: 400 });
    }

    // Responde 200 já; processa em background (Meta reentrega se demorar/falhar).
    ctx.waitUntil(
      (async () => {
        try {
          for (const entry of payload.entry ?? []) {
            for (const change of entry.changes ?? []) {
              const value = change.value;
              if (change.field === "messages") {
                if (value?.messages) await processarMensagem(env, value);
                if (value?.statuses) await processarStatus(env, value);
              } else if (change.field === "phone_number_quality_update") {
                await env.WA_DB.prepare("INSERT INTO wa_eventos (tipo,detalhe,raw) VALUES ('quality',?,?)")
                  .bind(value?.current_limit ?? value?.event ?? "", JSON.stringify(value)).run();
              }
            }
          }
        } catch (e) {
          console.error("processamento falhou", e);
        }
      })(),
    );

    return new Response("EVENT_RECEIVED", { status: 200 });
  },
};
