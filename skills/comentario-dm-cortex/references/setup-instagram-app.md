# Como configurar o App no Meta Developer Dashboard

Tutorial passo a passo para criar o app que conecta seu Instagram com a automacao de DMs.

> Tutorial visual com prints: a documentação do Córtex OS

---

## 1. Criar o App

1. Acesse [developers.facebook.com](https://developers.facebook.com/)
2. Faça login com sua conta do Facebook (a mesma vinculada ao Instagram Business)
3. Clique em **My Apps** > **Create App**
4. Tipo de app: **Business**
5. Nome do app: qualquer coisa (ex: "Automacao DM")
6. Conta Business: selecione a sua (ou crie uma se nao tiver)
7. Clique em **Create App**

## 2. Adicionar o produto Instagram

1. No painel do app, vá em **Add Products**
2. Procure **Instagram** e clique em **Set Up**
3. Na sidebar, vai aparecer **Instagram > API setup with Instagram login**

## 3. Configurar permissoes

No painel do app, vá em **App Review > Permissions and Features**. Você precisa dessas 3 permissoes:

| Permissao | Pra que serve |
|-----------|---------------|
| `instagram_business_basic` | Ler dados da conta (posts, comentarios) |
| `instagram_manage_comments` | Responder comentarios publicamente |
| `instagram_business_manage_messages` | Enviar DMs (private reply) |

**Modo Development:** essas permissoes ja funcionam para contas de teste (sua propria conta). Nao precisa submeter para review para testar.

**Modo Live (producao):** para funcionar com qualquer conta, precisa submeter cada permissao para review da Meta. Mas para uso proprio, o modo Development ja basta.

## 4. Gerar o Token de Acesso

1. Vá em **Instagram > API setup with Instagram login**
2. Em **Generate access tokens**, selecione sua conta Instagram Business
3. Marque as 3 permissoes listadas acima
4. Clique em **Generate token**
5. Copie o token (comeca com `IGAA...`)

**IMPORTANTE:** esse token tem validade de 60 dias. Quando expirar, gere um novo aqui e atualize no Worker com `npx wrangler secret put INSTAGRAM_ACCESS_TOKEN`.

## 5. Pegar o Instagram Account ID

Na mesma tela de API setup, o Account ID aparece logo abaixo do token gerado. E um numero tipo `17841447368297614`.

Se nao achar, pode buscar via API:
```
GET https://graph.instagram.com/v22.0/me?fields=id,username&access_token=SEU_TOKEN
```

## 6. Configurar o Webhook

**Essa parte você faz DEPOIS do deploy do Worker** (o setup guiado da skill cuida disso).

1. No painel do app, vá em **Webhooks** na sidebar
2. Clique em **Add Subscription** > selecione **Instagram**
3. Preencha:
   - **Callback URL:** `https://seu-worker.workers.dev/webhook`
   - **Verify Token:** o token de verificacao que o setup gerou
4. Clique em **Verify and Save**
5. Na lista de campos, ative **comments** (clique em Subscribe)

## 7. Politica de Privacidade

O Meta exige uma URL de politica de privacidade para apps que usam a API do Instagram.

Opcoes:
- **Gerar automaticamente:** a skill pode gerar uma pagina HTML basica e hospedar no Cloudflare Pages
- **Usar um servico:** [privacypolicygenerator.info](https://www.privacypolicygenerator.info/) gera uma gratis
- **Colar qualquer URL:** se você ja tem um site com politica de privacidade, pode usar

Onde configurar: no painel do app, **Settings > Basic > Privacy Policy URL**.

## 8. Publicar o App (opcional)

- **Modo Development:** funciona para sua propria conta. Basta adicionar sua conta como testador em **Roles > Instagram Testers**.
- **Modo Live:** necessario se você quiser que outras contas usem o app. Requer review das permissoes.

Para uso proprio (tipo ManyChat para você mesmo), o modo Development resolve.

## Troubleshooting

### "O webhook nao recebe eventos"
- Verifique se o app esta em modo **Live** OU se sua conta esta como **Instagram Tester**
- Verifique se o campo **comments** esta com Subscribe ativo
- Verifique se o Verify Token bate com o configurado no Worker

### "Erro 190: Invalid OAuth access token"
- Token expirou (dura 60 dias). Gere um novo e atualize no Worker:
  ```bash
  echo "NOVO_TOKEN" | npx wrangler secret put INSTAGRAM_ACCESS_TOKEN
  ```

### "Erro 10: Permission denied"
- Falta permissao. Verifique se as 3 permissoes estao ativas no app
- Se estiver em modo Development, verifique se sua conta e testadora

### "DM nao chega mas comentario ta sendo detectado"
- Provavelmente falta a permissao `instagram_business_manage_messages`
- Ou a pessoa nao segue seu perfil (DM vai para "Solicitacoes")
