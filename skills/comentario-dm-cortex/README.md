# Comentario DM Córtex

Skill de automacao de DM no Instagram para Claude Code. Quando alguem comenta uma keyword em um post, envia DM automatica + responde o comentario publicamente. Tipo um ManyChat simplificado, rodando no Cloudflare Workers (gratis).

**Componentes:**
- **Cloudflare Worker** — recebe webhooks do Instagram e envia DMs em tempo real
- **KV Storage** — armazena as automacoes ativas
- **Claude Code** — interface conversacional pra gerenciar tudo

## Instalacao rapida

```bash
# 1. Copiar a skill pra pasta do Claude Code
cp -r . ~/.claude/skills/comentario-dm-cortex/

# 2. Rodar o setup guiado
# No Claude Code, digite: /comentario-dm-cortex setup
```

O setup guiado cuida de tudo: instalar wrangler, configurar o Cloudflare, fazer o deploy e conectar o webhook. Você só precisa ter criado o app no Meta Developer Dashboard antes.

### Pre-requisitos

1. **Conta Instagram Business** (nao funciona com conta pessoal)
2. **App no Meta Developer Dashboard** — tutorial: a documentação do Córtex OS
3. **Node.js** instalado (pra rodar o wrangler)
4. **Conta no Cloudflare** (gratis) — tutorial: a documentação do Córtex OS

## Uso

Depois de instalada, a skill e ativada automaticamente quando você fala com o Claude Code sobre automacao de DM. Exemplos:

- "cria automacao pro post X, keyword LINK, mensagem com o link do curso"
- "lista minhas automacoes"
- "remove automacao do post X"
- "manda retroativo pros comentarios antigos do post Y"

### Criar automacao

Você passa a URL do post, a keyword e a mensagem. O Claude converte a URL pro media_id, registra no Worker e confirma.

```
> cria automacao pro instagram.com/p/ABC123
> keyword: LINK
> mensagem: "Aqui está o link que você pediu: https://exemplo.com"
```

### Retroativo

Envia DMs pra quem ja comentou a keyword em posts antigos (antes da automacao existir).

```
> manda retroativo pros comentarios do post instagram.com/p/ABC123, keyword LINK
```

O Claude busca os comentarios, mostra a lista e pede a sua confirmacao antes de enviar.

## Estrutura

```
comentario-dm-cortex/
├── SKILL.md                    # Instrucoes pro Claude (orquestrador)
├── README.md                   # Esse arquivo
├── .gitignore
├── .env                        # Tokens e config (gerado no setup, gitignored)
├── contas.yaml                 # Cadastro de contas Instagram
├── aprendizados.md             # Memoria persistente do Claude
├── references/
│   ├── setup-instagram-app.md  # Tutorial Meta Developer Dashboard
│   └── setup-cloudflare.md     # Tutorial Cloudflare
└── worker/
    ├── src/
    │   └── index.js            # Codigo do Cloudflare Worker
    ├── wrangler.toml.template  # Template de config (com placeholders)
    ├── wrangler.toml            # Config real (gerada no setup, gitignored)
    └── package.json
```

## Disclaimer: use com responsabilidade

Essa skill foi **vibe-codada com Claude Code** a partir da documentacao oficial da [Instagram Graph API](https://developers.facebook.com/docs/instagram-platform) e do [Cloudflare Workers](https://developers.cloudflare.com/workers/). E um projeto experimental.

**Pontos importantes antes de usar:**

- **Use por sua conta e risco.** A gente nao garante que o uso dessa skill nao vai resultar em restricoes, bloqueios ou qualquer problema na sua conta do Instagram. O Meta tem politicas proprias sobre automacao e pode mudar as regras a qualquer momento.
- **Leia as politicas do Instagram.** Antes de usar qualquer automacao, entenda os [Termos de Uso da Plataforma Instagram](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/overview#terms-and-policies) e as regras de rate limiting. A skill inclui delays e boas praticas, mas isso nao e garantia de nada.
- **Revise o codigo.** Essa skill envia mensagens pela sua conta do Instagram. Antes de usar, olhe o codigo do Worker (`worker/src/index.js`) pra entender o que cada operacao faz. E open source justamente pra isso.
- **Token tem validade.** O token de acesso do Instagram expira a cada 60 dias. Quando expirar, gere um novo e atualize no Worker.
- **Sem garantia de funcionamento.** A API do Instagram muda com frequencia. Algo que funciona hoje pode quebrar amanha.

Em resumo: e uma ferramenta pratica, mas você e o responsavel pelo que acontece na sua conta. Use com consciencia e nao faca nada que você nao faria manualmente.

## Criado por

Córtex OS — Venda Mais com Conteúdo

## Licença e proveniência

Open source sob **MIT** (ver [LICENSE](LICENSE)). Gratuito: o valor está na
implementação, não no código. Inspirado no projeto **Ratos de IA**
(ratosdeia.com.br) e atualizado pela comunidade open source. Detalhes em
[NOTICE.md](NOTICE.md).
