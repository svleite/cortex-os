# Aprendizados: WhatsApp Atendimento (Cloud API)

- **subscribed_apps é a armadilha nº1.** Configurar o webhook no painel não basta: a WABA precisa ser inscrita no app (`POST /<WABA_ID>/subscribed_apps`). Sem isso o webhook fica mudo, sem erro nenhum.

- **Token do painel expira.** Pra produção, crie um System User com token permanente (escopos `whatsapp_business_messaging` + `whatsapp_business_management`).

- **BM com identidade errada = ban.** Se o Business Manager estiver verificado com o nome de outra empresa, a WABA é rejeitada/banida. Use BM com o CNPJ do próprio negócio.

- **Janela de 24h.** Responder dentro de 24h da mensagem do cliente é grátis. Iniciar fora disso exige template aprovado, e a Meta classifica o template pelo conteúdo (tentar "abrir conversa" vira MARKETING). Anúncio Click-to-WhatsApp mantém tudo na janela: custo zero.

- **9º dígito BR.** A Meta entrega o número sem o 9. Recompor antes de gravar/enviar (`normalizarTelefoneBR`), senão dá conversa duplicada e envio falho.

- **Responda o webhook com 200 na hora.** Processe em background (`ctx.waitUntil`). Se demorar, a Meta reentrega o evento e você duplica. Dedupe por `wa_id`.

- **Valide a assinatura.** `X-Hub-Signature-256` com HMAC do App Secret, comparação em tempo constante. Sem isso qualquer um posta no seu webhook.

- **Handoff por tag no texto.** O bot termina com `[HANDOFF]` (removido antes do envio); o Worker marca a conversa como `humano` e para de responder. Simples e confiável, sem function calling.

- **Multimodal sai barato.** Áudio via Workers AI Whisper (free tier), imagem direto no Claude (visão). Não precisa de serviço externo.

- **Número de teste primeiro.** A Meta dá um número grátis (até 5 destinatários). Valide tudo nele antes de queimar o chip de produção (que vira API-only e não volta atrás fácil).
