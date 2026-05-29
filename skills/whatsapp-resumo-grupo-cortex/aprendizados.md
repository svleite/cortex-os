# Aprendizados: WhatsApp Resumo de Grupo

Decisões e armadilhas que valem lembrar.

- **API oficial não lê grupo.** WhatsApp Cloud API (Meta) é só 1:1 empresa↔cliente. Ler grupo exige biblioteca não-oficial (Evolution/Baileys). Não tem como contornar isso pelo caminho oficial.

- **Risco de ban é do número, não do código.** Toda solução não-oficial fala o protocolo do WhatsApp Web e viola o ToS. Use número descartável; nunca o principal/WABA.

- **PULL > PUSH pra digest diário.** O Evolution já persiste as mensagens no Postgres dele. Puxar as 24h na hora do resumo (`/chat/findMessages`) é mais simples que receber tudo por webhook e manter um store próprio. Menos peça, menos falha. (Vale store próprio só se quiser histórico longo / re-resumo.)

- **Always-on, não serverless.** A conexão do Evolution é um processo vivo 24/7. Cloudflare Workers / Lambda não seguram isso. Precisa de VPS. Latência não importa (1x/dia).

- **Destino define a discrição.** Postar de volta no grupo = todo mundo vê. Discord (webhook/bot) = acompanhamento silencioso. Escolha conforme o caso (e o consentimento de quem está no grupo).

- **Custo é trivial.** Evolution grátis (só a VPS), Claude Haiku resume um dia de grupo por centavos. Suba pra Sonnet só se a qualidade do resumo decepcionar.

- **Gotcha findMessages:** o shape da resposta varia entre versões do Evolution v2. O app normaliza alguns formatos; confira no primeiro teste real.

- **Origem:** padrão inspirado em um post da comunidade Ratos de IA (Evolution API + Claude + agendador).
