# Como configurar o Cloudflare Workers

Tutorial para criar a conta no Cloudflare e ter tudo pronto para o deploy do Worker.

> Tutorial visual com prints: a documentação do Córtex OS

---

## 1. Criar a conta

1. Acesse [cloudflare.com](https://www.cloudflare.com/)
2. Clique em **Sign Up**
3. Crie a conta com email e senha
4. Confirme o email

**O plano Free já inclui tudo que você precisa:** Workers (100k requests/dia), KV Storage, e deploy ilimitado.

## 2. Pegar o Account ID

1. Depois de logar, vá no dashboard do Cloudflare
2. Na sidebar, clique em **Workers & Pages**
3. O **Account ID** aparece na sidebar direita (ou na URL: `dash.cloudflare.com/ACCOUNT_ID/workers`)
4. Copie esse ID, você vai precisar no setup

Alternativa via terminal (se já tiver o wrangler logado):
```bash
npx wrangler whoami
```
O Account ID aparece no output.

## 3. Instalar o Wrangler (CLI do Cloudflare)

```bash
npm install -g wrangler
```

Verificar instalação:
```bash
npx wrangler --version
```

## 4. Logar no Wrangler

```bash
npx wrangler login
```

Isso abre o navegador para você autorizar. Depois de autorizar, o terminal confirma o login.

Verificar:
```bash
npx wrangler whoami
```

## 5. O que o setup da skill faz automaticamente

Depois de logar no Wrangler e ter o Account ID, o setup guiado da skill cuida de:

1. **Criar o KV Namespace** — armazenamento das automações
2. **Gerar o wrangler.toml** — config do Worker com seus IDs
3. **Configurar os secrets** — tokens ficam encriptados no Cloudflare
4. **Fazer o deploy** — publica o Worker e retorna a URL

Você não precisa mexer no dashboard do Cloudflare para nada disso.

## Troubleshooting

### "Erro: You must be logged in"
```bash
npx wrangler login
```

### "Erro: Account not found"
- Verifique se o Account ID está correto
- Verifique se a conta tem o plano Free ativo (não precisa de plano pago)

### "Erro: KV namespace not found"
- O namespace precisa ser criado antes do deploy. O setup da skill faz isso automaticamente.

### Limites do plano Free
- **100.000 requests por dia** — mais que suficiente para automação de DMs
- **KV:** 100.000 leituras/dia, 1.000 escritas/dia
- **Worker:** 10ms CPU time por request (sobra bastante)
