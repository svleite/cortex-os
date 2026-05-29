# Aprendizados — Comentario DM Córtex

<!-- O Claude registra aqui erros, descobertas e regras aprendidas durante o uso.
     Formato:
     ### {DATA} — {titulo curto}
     **Regra:** {o que fazer sempre/nunca}
     **Contexto:** {o que aconteceu pra gerar esse aprendizado}
-->

### 2026-05-13 — App precisa estar "Ao vivo" pra entregar webhooks reais
**Regra:** Após criar app no Meta Developer e configurar webhook, mudar Modo do aplicativo de "Desenvolvimento" pra "Ao vivo". Em dev, só o botão Teste dispara webhook sintético; comentários reais NÃO chegam no Worker mesmo de contas testadoras.
**Contexto:** Setup @samuelleite. Webhook verde, comments assinado, tester aceito, mas comentários reais não acionavam. Mudar pra Live resolveu na hora.

### 2026-05-13 — Subscribed_fields default vem só com "messages"
**Regra:** Após adicionar conta IG no app, chamar `POST /v22.0/{ig_id}/subscribed_apps?subscribed_fields=comments,messages,live_comments` via API. Toggle visual no card 1 do Meta não garante que "comments" foi inscrito.
**Contexto:** Apesar do toggle "Assinatura do webhook" ativo no painel, GET subscribed_apps mostrava só ["messages"]. Forçar via API resolveu.

### 2026-05-13 — Endpoint correto pra listar media é /me/media
**Regra:** Pra encontrar media_id de um post via shortcode, usar `GET /v22.0/{ig_id}/media?fields=id,shortcode&limit=50`. Não usar business_discovery pra conta própria.
**Contexto:** business_discovery falhou retornando vazio. /me/media listou tudo direto.
