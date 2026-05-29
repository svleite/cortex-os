# WhatsApp Atendimento: Córtex

Skill do Córtex OS que monta um **bot de atendimento no WhatsApp** via API oficial da Meta (Cloud API).

O cliente manda mensagem, o bot responde com Claude usando a sua base de conhecimento, transcreve áudio e lê imagem, e quando a conversa esquenta (pedido de preço, intenção de fechar) passa pra um humano e avisa o time. Tudo persistido em D1.

## Como funciona

```
Meta Cloud API --webhook--> Cloudflare Worker --> Claude responde
                                |
                                └─ handoff: marca 'humano' + avisa o time (botão Assumir / e-mail)
```

Sem servidor: Cloudflare Worker + D1 + Workers AI (Whisper) + Claude.

## Importante

- É a API **oficial** da Meta: conversa **1:1** (empresa↔cliente). **Não lê grupos** (pra isso use `whatsapp-resumo-grupo-cortex`).
- Responder dentro de 24h após o cliente escrever é **grátis**. Ver `references/custo-e-janela.md`.
- Precisa de Business Manager próprio + domínio no Cloudflare + chave Anthropic.

## Começar

Peça ao Claude: **"/whatsapp-atendimento-cortex setup"**. Ele guia o setup fase por fase (Meta, Cloudflare, base de conhecimento, webhook, teste).

Conteúdo:
- `SKILL.md`: instruções (lidas pelo Claude)
- `worker/`: o Worker (webhook, bot, D1)
- `references/`: setup Meta, setup Cloudflare, custo

## Licença

MIT (ver `LICENSE`). Inspirado na comunidade Ratos de IA. Ver `NOTICE.md`.
