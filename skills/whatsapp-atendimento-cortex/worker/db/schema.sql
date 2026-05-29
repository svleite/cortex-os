-- whatsapp-atendimento — esquema D1
-- Aplicar: wrangler d1 execute SEU_DB --file=db/schema.sql --remote

-- Uma conversa por número (E.164 sem +, já com 9º dígito recomposto no BR).
CREATE TABLE IF NOT EXISTS wa_conversas (
  telefone     TEXT PRIMARY KEY,             -- 55DDDNNNNNNNNN
  nome         TEXT,                          -- profile.name que a Meta entrega
  status       TEXT NOT NULL DEFAULT 'bot',  -- bot | humano | fechado
  origem       TEXT,                          -- ctwa (click-to-whatsapp) | organico | desconhecido
  assumido_por TEXT,                          -- nome do atendente que assumiu (claim)
  primeiro_em  TEXT NOT NULL DEFAULT (datetime('now')),
  ultimo_em    TEXT NOT NULL DEFAULT (datetime('now')),
  ultima_msg   TEXT,                          -- preview da última mensagem
  janela_ate   TEXT                           -- fim da janela 24h de serviço (grátis pra responder)
);

-- Toda mensagem (entrada e saída). wa_id deduplica reentregas da Meta.
CREATE TABLE IF NOT EXISTS wa_mensagens (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  wa_id     TEXT UNIQUE,                       -- id da mensagem (messages[].id ou wamid de saída)
  telefone  TEXT NOT NULL,
  direcao   TEXT NOT NULL,                     -- in | out
  autor     TEXT NOT NULL DEFAULT 'cliente',   -- cliente | bot | humano
  tipo      TEXT NOT NULL DEFAULT 'text',      -- text | image | audio | button | interactive | ...
  texto     TEXT,
  raw       TEXT,                              -- JSON cru do evento (debug/auditoria)
  criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_msg_tel ON wa_mensagens(telefone, criado_em);

-- Eventos de saúde/status (quality update, status de entrega, sistema, erros).
CREATE TABLE IF NOT EXISTS wa_eventos (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  tipo      TEXT NOT NULL,                     -- quality | status | sistema | erro
  detalhe   TEXT,
  raw       TEXT,
  criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
