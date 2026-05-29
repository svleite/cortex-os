# Subir e parear o Evolution API

Evolution API é open-source e self-host. **Não tem cadastro.** A única chave é a `EVOLUTION_API_KEY` que você inventa no `.env`.

## 1. Subir o stack

Copie a pasta `app/` desta skill pra VPS:

```bash
rsync -avz -e "ssh -i ~/.ssh/sua-chave.key" \
  --exclude node_modules --exclude .env \
  app/ usuario@SEU_IP:~/whatsapp-resumo/

ssh -i ~/.ssh/sua-chave.key usuario@SEU_IP
cd ~/whatsapp-resumo
cp .env.example .env
nano .env        # preencher senhas, EVOLUTION_API_KEY, ANTHROPIC_API_KEY, DESTINO
docker compose up -d --build
docker compose logs -f evolution
```

## 2. Parear o número (scan de QR, uma vez)

O Evolution fica só no localhost. Abra um túnel SSH da sua máquina:

```bash
ssh -i ~/.ssh/sua-chave.key -L 8080:127.0.0.1:8080 usuario@SEU_IP
```

Com o túnel aberto, na sua máquina:

```bash
# criar a instância
curl -X POST http://127.0.0.1:8080/instance/create \
  -H "apikey: SUA_EVOLUTION_API_KEY" -H "Content-Type: application/json" \
  -d '{"instanceName":"default","integration":"WHATSAPP-BAILEYS","qrcode":true}'

# pegar o QR (ou abrir o Manager em http://127.0.0.1:8080/manager)
curl http://127.0.0.1:8080/instance/connect/default -H "apikey: SUA_EVOLUTION_API_KEY"
```

Escaneie o QR no WhatsApp do **número dedicado** (Aparelhos conectados). A conexão fica viva no servidor; o celular pode ser guardado (mas mantenha o número ativo pra receber SMS de re-verificação).

## 3. Descobrir os JIDs dos grupos

Depois que o número entrar nos grupos:

```bash
curl http://127.0.0.1:8080/group/fetchAllGroups/default?getParticipants=false \
  -H "apikey: SUA_EVOLUTION_API_KEY"
```

Pegue o `id` de cada grupo (formato `...@g.us`).

## Gotchas

- **Formato do `findMessages`** muda um pouco entre versões do Evolution v2. O app normaliza `messages.records` / `records` / array; se a sua versão retornar outro shape, ajuste em `app/index.js` (`fetchLast24h`).
- **Número banido?** É o risco do não-oficial. Por isso o número é descartável. Se cair, crie outro chip, repare, recadastre os grupos.
- **Sessão perdida** (re-scan de QR): mantenha a VPS estável; o Evolution persiste as credenciais no Postgres.
