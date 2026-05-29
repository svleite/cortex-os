# Córtex OS

**Sistema operacional de negócio para Venda Mais com Conteúdo.**

Coleção de skills para o [Claude Code](https://claude.com/claude-code) que
operam tráfego pago, analytics, automação e conteúdo de ponta a ponta. Pensado
para founders, agências e operações que querem rodar marketing orientado a dados
sem reinventar a roda.

Open source e **gratuito**. Sinta-se livre para modificar e repassar livremente sob MIT.

## Skills

| Skill | O que faz |
|-------|-----------|
| `ads-cortex` | Inteligência de tráfego pago: diagnóstico, relatório, auditoria, Health Score |
| `meta-ads-cortex` | Gestão de campanhas Meta Ads (Facebook/Instagram) via SDK oficial |
| `google-ads-cortex` | Gestão de campanhas Google Ads via SDK oficial (GAQL) |
| `ga4-cortex` | Leitura de Google Analytics 4 (sessões, conversões, fontes, realtime) |
| `ga4-setup-cortex` | Cria propriedades GA4 + web data stream |
| `gsc-cortex` | Google Search Console: indexação, sitemaps, queries, redirects |
| `gtm-cortex` | Gerencia containers Google Tag Manager via API REST |
| `comentario-dm-cortex` | Automação de DM no Instagram por comentário (tipo ManyChat) |
| `rd-station-cortex` | Leitura de leads e funil do RD Station Marketing |

## Instalação

Cada skill é uma pasta independente. Copie a que precisar para `~/.claude/skills/`:

```bash
git clone https://github.com/svleite/cortex-os
cp -r cortex-os/ads-cortex ~/.claude/skills/ads-cortex
```

Cada skill traz seu próprio `SKILL.md` (instruções), `README.md` (setup) e
`.env.example` quando aplicável. Credenciais ficam em `.env` local, nunca versionado.

## Filosofia

Este código não está à venda. O Córtex OS é livre e fica público para qualquer pessoa
usar, igual ao que nos inspirou. Quem quiser ajuda para implementar em operações
específicas.

## Licença e proveniência

Open source sob **MIT** (ver [LICENSE](LICENSE)). Inspirado no projeto
**Ratos de IA** (ratosdeia.com.br) e atualizado pela comunidade open source de
skills do Claude Code. Detalhes em [NOTICE.md](NOTICE.md).
