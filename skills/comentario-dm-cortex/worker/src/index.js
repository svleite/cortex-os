/**
 * Instagram DM Automation Worker — Córtex OS
 *
 * Recebe webhooks de comentarios do Instagram.
 * Se o comentario contem a keyword configurada, envia DM (private reply) automaticamente.
 *
 * Automacoes ficam no KV namespace AUTOMATIONS:
 *   key: "post:<MEDIA_ID>" → { keyword, message, comment_replies, active, created_at }
 *   key: "index" → [{ media_id, keyword, message, comment_replies, active, created_at, label }]
 */

const IG_API = "https://graph.instagram.com/v22.0";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // --- Webhook verification (GET) ---
    if (request.method === "GET" && url.pathname === "/webhook") {
      const mode = url.searchParams.get("hub.mode");
      const token = url.searchParams.get("hub.verify_token");
      const challenge = url.searchParams.get("hub.challenge");

      if (mode === "subscribe" && token === env.INSTAGRAM_WEBHOOK_VERIFY_TOKEN) {
        return new Response(challenge, { status: 200 });
      }
      return new Response("Forbidden", { status: 403 });
    }

    // --- Webhook events (POST) ---
    if (request.method === "POST" && url.pathname === "/webhook") {
      const body = await request.json();
      // Processa em background (Meta espera resposta rapida)
      ctx.waitUntil(this.handleWebhook(body, env));
      return new Response("OK", { status: 200 });
    }

    // --- API: listar automacoes ---
    if (request.method === "GET" && url.pathname === "/automations") {
      const auth = url.searchParams.get("key");
      if (auth !== env.INSTAGRAM_WEBHOOK_VERIFY_TOKEN) {
        return new Response("Unauthorized", { status: 401 });
      }
      const index = await env.AUTOMATIONS.get("index", "json") || [];
      return Response.json(index);
    }

    // --- API: criar/atualizar automacao ---
    if (request.method === "POST" && url.pathname === "/automations") {
      const auth = url.searchParams.get("key");
      if (auth !== env.INSTAGRAM_WEBHOOK_VERIFY_TOKEN) {
        return new Response("Unauthorized", { status: 401 });
      }

      const { media_id, keyword, message, comment_replies, label } = await request.json();
      if (!media_id || !keyword || !message) {
        return Response.json({ error: "media_id, keyword e message sao obrigatorios" }, { status: 400 });
      }

      const automation = {
        keyword: keyword.toLowerCase().trim(),
        message,
        comment_replies: comment_replies || [
          "feito, enviado! confere tua DM 📩",
          "pronto, confere tua DM! 🐀",
          "mandei lá na DM!",
          "enviado! olha tua DM 👀",
        ],
        active: true,
        created_at: new Date().toISOString(),
        label: label || "",
      };

      // Salva no KV por media_id
      await env.AUTOMATIONS.put(`post:${media_id}`, JSON.stringify(automation));

      // Atualiza indice
      const index = await env.AUTOMATIONS.get("index", "json") || [];
      const existing = index.findIndex((a) => a.media_id === media_id);
      const entry = { media_id, ...automation };
      if (existing >= 0) {
        index[existing] = entry;
      } else {
        index.push(entry);
      }
      await env.AUTOMATIONS.put("index", JSON.stringify(index));

      return Response.json({ ok: true, automation: entry });
    }

    // --- API: deletar automacao ---
    if (request.method === "DELETE" && url.pathname === "/automations") {
      const auth = url.searchParams.get("key");
      if (auth !== env.INSTAGRAM_WEBHOOK_VERIFY_TOKEN) {
        return new Response("Unauthorized", { status: 401 });
      }

      const { media_id } = await request.json();
      if (!media_id) {
        return Response.json({ error: "media_id obrigatorio" }, { status: 400 });
      }

      await env.AUTOMATIONS.delete(`post:${media_id}`);

      const index = await env.AUTOMATIONS.get("index", "json") || [];
      const filtered = index.filter((a) => a.media_id !== media_id);
      await env.AUTOMATIONS.put("index", JSON.stringify(filtered));

      return Response.json({ ok: true, removed: media_id });
    }

    return new Response("Instagram DM Worker — Córtex OS", { status: 200 });
  },

  async handleWebhook(body, env) {
    if (!body.entry) return;

    for (const entry of body.entry) {
      if (!entry.changes) continue;

      for (const change of entry.changes) {
        if (change.field !== "comments") continue;

        const { text, id: commentId, media, from } = change.value;
        if (!text || !commentId || !media?.id) continue;

        // Ignora comentarios do proprio perfil
        if (from?.id === env.INSTAGRAM_ACCOUNT_ID) continue;

        // Busca automacao pra esse post
        const automation = await env.AUTOMATIONS.get(`post:${media.id}`, "json");
        if (!automation || !automation.active) continue;

        // Checa keyword (case insensitive, contem a palavra)
        const commentText = text.toLowerCase().trim();
        const keyword = automation.keyword.toLowerCase().trim();
        if (!commentText.includes(keyword)) continue;

        // Envia DM via private reply
        await this.sendPrivateReply(commentId, automation.message, env);

        // Responde o comentario com mensagem rotacionada
        if (automation.comment_replies?.length > 0) {
          const reply = this.pickRandom(automation.comment_replies);
          await this.replyToComment(commentId, reply, env);
          console.log(`Resposta no comentario: "${reply}"`);
        }

        console.log(`DM enviada: comment=${commentId}, user=${from?.username}, keyword="${keyword}"`);
      }
    }
  },

  pickRandom(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  },

  async replyToComment(commentId, text, env) {
    const url = `${IG_API}/${commentId}/replies`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.INSTAGRAM_ACCESS_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: text }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error(`Erro ao responder comentario: ${response.status} — ${error}`);
    }

    return response;
  },

  async sendPrivateReply(commentId, messageText, env) {
    const url = `${IG_API}/${env.INSTAGRAM_ACCOUNT_ID}/messages`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.INSTAGRAM_ACCESS_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        recipient: { comment_id: commentId },
        message: { text: messageText },
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error(`Erro ao enviar DM: ${response.status} — ${error}`);
    }

    return response;
  },
};
