# Córtex OS

**Sistema operacional de negócio para Venda Mais com Conteúdo, dentro do [Claude Code](https://claude.com/claude-code).**

Não é uma coleção solta de skills. É um OS: um shell de comandos (`/setup`, `/mapear`,
`/iniciar`, `/atualizar`, `/syncar`) que configura o ambiente pro seu negócio, mais um
conjunto de skills de execução (tráfego pago, analytics, automação, conteúdo).

Open source e **gratuito**. Sinta-se livre para modificar e repassar livremente sob MIT.

## Instalação

Um comando (clona em `~/.cortex-os` e linka tudo em `~/.claude/`):

```bash
curl -fsSL https://raw.githubusercontent.com/svleite/cortex-os/main/install.sh | bash
```

Depois, abra o Claude Code e rode **`/setup`**.

> A instalação usa **symlink**, não cópia. Isso é de propósito: quando o Córtex OS é
> atualizado, um `git pull` reflete na sua ferramenta na hora, sem reinstalar.

## Atualizar

```bash
cd ~/.cortex-os && git pull && ./install.sh
```

(ou rode o one-liner de instalação de novo, é idempotente). Como as skills são
symlinks pro `~/.cortex-os`, o pull já atualiza o que você usa. O `install.sh` só
re-linka skills/comandos novos que tenham surgido.

## O shell do OS (comandos)

| Comando | O que faz |
|---------|-----------|
| `/setup` | Onboarding: configura CLAUDE.md, memória e estrutura pro seu negócio |
| `/mapear` | Entrevista seus processos repetitivos e cria skills sob medida |
| `/iniciar` | Abre a sessão lendo contexto e propondo foco |
| `/atualizar` | Reconcilia o workspace com a documentação (manutenção de contexto) |
| `/novo-projeto` | Cria pasta de projeto novo com CLAUDE.md próprio |
| `/syncar` | Salva o workspace no GitHub (commit + push) |

## As skills de execução

| Skill | O que faz |
|-------|-----------|
| `ads-cortex` | Inteligência de tráfego pago: diagnóstico, relatório, auditoria, Health Score |
| `meta-ads-cortex` | Gestão de campanhas Meta Ads (Facebook/Instagram) via SDK oficial |
| `google-ads-cortex` | Gestão de campanhas Google Ads via SDK oficial (GAQL) |
| `ga4-cortex` | Leitura de Google Analytics 4 (sessões, conversões, fontes, realtime) |
| `ga4-setup-cortex` | Cria propriedades GA4 + web data stream |
| `gsc-cortex` | Google Search Console: indexação, sitemaps, queries, redirects |
| `gtm-cortex` | Gerencia containers Google Tag Manager via API REST |
| `comentario-dm-cortex` | Automação de DM no Instagram por comentário |
| `rd-station-cortex` | Leitura de leads e funil do RD Station Marketing |

Cada skill traz `SKILL.md` (instruções) e `README.md` (setup). Credenciais ficam em
`.env` local de cada skill, **nunca versionado**.

## Estrutura do repo

```
cortex-os/
├── install.sh        # instala e atualiza (symlink)
├── skills/           # as 9 skills de execução
├── commands/         # o shell do OS (slash-commands)
├── templates/        # perfis, skills-modelo, catálogo de ferramentas
├── README.md
├── LICENSE           # MIT
└── NOTICE.md         # proveniência
```

## Filosofia

Este código não está à venda. O Córtex OS é livre e público, igual ao que nos inspirou.
Quem quiser ajuda pra implementar em operações específicas.

## Licença e proveniência

Open source sob **MIT** (ver [LICENSE](LICENSE)). Atualizado pela comunidade open
source de skills do Claude Code. Detalhes em [NOTICE.md](NOTICE.md).
