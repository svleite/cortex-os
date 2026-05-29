# Setup na Meta (WhatsApp Cloud API)

A Cloud API é a API **oficial** da Meta, hospedada de graça por ela. É só pra conversa **1:1** (empresa↔cliente); não lê grupos. O número vira "API-only": ninguém abre o WhatsApp no celular com ele, tudo passa pelo Worker.

## 1. App + WABA + número de teste

1. `developers.facebook.com` > criar app tipo **Empresa**, vincular ao seu **Business Manager**. Anote o **App ID**.
2. **Adicionar produto > WhatsApp > Configurar.** Aceite os termos, escolha/crie a **WABA**. Anote o **WABA ID**.
3. A Meta libera um **número de teste** grátis (envia só pra até 5 números pré-cadastrados). Cadastre seu celular. Anote o **Phone Number ID**.
4. **App Secret:** Configurações > Básico > App Secret. Vira `WA_APP_SECRET`.
5. **Token:** o **token temporário** do painel serve pro teste (expira em horas). Pra produção, crie um **System User** com token permanente (passo 4).

## 2. ARMADILHA: subscribed_apps (sem isso o webhook fica MUDO)

Configurar o webhook no painel NÃO basta. A WABA precisa ser **inscrita no app**:

```bash
curl -X POST "https://graph.facebook.com/v22.0/<WABA_ID>/subscribed_apps" \
  -H "Authorization: Bearer <WA_TOKEN>"
```

Ou no painel: toggle **"Assinar webhooks"** no quadro da conta. Se o bot não recebe nada e não dá erro, é quase sempre isto.

## 3. Webhook (depois do deploy do Worker)

No app Meta > WhatsApp > Configuração > Webhooks:
- **Callback URL:** `https://wa.SEUDOMINIO.com/webhook`
- **Verify token:** o mesmo valor de `WA_VERIFY_TOKEN`.
- Assine o campo **`messages`** (e `phone_number_quality_update` pra saúde da conta).

## 4. Token permanente (produção): System User

O token do painel expira. Pra produção:
1. Business Manager > Configurações > Usuários > **Usuários do sistema** > criar (papel admin).
2. **Adicionar ativos:** dê acesso à WABA e ao app.
3. **Gerar token** com escopos `whatsapp_business_messaging` + `whatsapp_business_management`. Marque como **sem expiração**.
4. Esse token vira o `WA_TOKEN` de produção.

## 5. Verificação de negócio e limites

- Sem verificação de negócio aprovada, o número fica em **250 conversas iniciadas/24h**. Suficiente pra começar.
- **Cuidado com o nome/identidade do BM:** se o Business Manager estiver verificado com nome de OUTRA empresa, a WABA pode ser **rejeitada/banida**. Use um BM com o CNPJ/identidade do próprio negócio.
- Faça a verificação de negócio pra subir os limites quando for pra produção.

## 6. Cutover do chip de produção (quando sair do número de teste)

Pra usar um número real (que hoje tem WhatsApp normal):
1. **Exclua a conta de WhatsApp daquele número** no app/celular ANTES de registrar na Cloud API.
2. Registre o número na WABA (recebe código por SMS/voz).
3. O número vira API-only. Não dá mais pra usar o app comum com ele.

## 7. Notas

- **9º dígito BR:** a Meta entrega o número **sem o 9**; o Worker recompõe em `normalizarTelefoneBR()` antes de gravar/enviar.
- **Qualidade do número:** o evento `phone_number_quality_update` (GREEN/YELLOW/RED) é gravado em `wa_eventos`. Fique de olho.
