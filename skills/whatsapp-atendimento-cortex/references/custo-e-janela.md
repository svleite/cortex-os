# Custo e a janela de 24h

| Situação | Custo |
|---|---|
| Cliente te manda mensagem e você responde **dentro de 24h** | **Grátis** (mensagem de serviço) |
| Você **inicia** conversa (fora da janela de 24h) | Pago: exige um **template aprovado** |

- Franquia mensal: **1.000 conversas de serviço grátis**.
- Templates pagos têm 2 categorias:
  - **UTILITY** (~R$0,04): aviso transacional concreto ("sua consulta está confirmada para 25/03 às 14h").
  - **MARKETING** (~R$0,34): qualquer coisa promocional ou "primeiro contato pra puxar conversa".

> A Meta classifica o template pelo **conteúdo**, não pelo que você marca. Um template tentando "abrir conversa com lead" quase sempre vira MARKETING.

## A jogada de custo zero

Se os anúncios forem **Click-to-WhatsApp**, o cliente sempre **inicia** a conversa. Tudo cai na janela de 24h: **grátis, sem template, pra sempre.** É o caso ideal pra um bot inbound como este.

## Sobre o template de handoff (opcional)

O Worker tem suporte a um template Utility no handoff (`WA_TEMPLATE_HANDOFF`), mas só faz sentido se você tiver um template aprovado e o handoff acontecer fora da janela. Por padrão, o bot responde com texto normal (dentro da janela, grátis). Deixe `WA_TEMPLATE_HANDOFF` vazio se não tiver template.
