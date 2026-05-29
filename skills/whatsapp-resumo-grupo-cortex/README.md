# WhatsApp Resumo de Grupo: Córtex

Skill do Córtex OS que monta um bot pra **resumir grupos de WhatsApp** todo dia com Claude.

O bot puxa as mensagens das últimas 24h de um ou mais grupos, gera um resumo executivo via Claude e entrega num destino à sua escolha: o próprio grupo, um canal do Discord, ou outro.

## Como funciona

```
[cron diário]  →  [Evolution API: puxa 24h do grupo]  →  [Claude: resume]  →  [destino]
```

Tudo numa VPS, num único `docker compose` (Evolution API + Postgres + Redis + app de resumo).

## Importante

- **API oficial da Meta não lê grupos.** Esta skill usa **Evolution API** (não-oficial, self-host). Isso viola o ToS do WhatsApp e o número **pode ser banido**: use sempre um **número dedicado e descartável**.
- Evolution é open-source: **não tem cadastro**, a única chave é uma que você inventa.
- Precisa de **VPS always-on** (não roda em serverless).

## Começar

Peça ao Claude: **"/whatsapp-resumo-grupo-cortex setup"**: ele guia o setup fase por fase (pré-condições → subir stack → parear número → mapear grupos → testar).

Conteúdo:
- `SKILL.md`: instruções da skill (lidas pelo Claude)
- `app/`: `docker-compose.yml` + código do bot
- `references/`: tutoriais de VPS, Evolution e destino
- `aprendizados.md`: decisões e armadilhas

## Licença

MIT (ver `LICENSE`). Inspirado na comunidade Ratos de IA. Ver `NOTICE.md`.
