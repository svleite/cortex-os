# Ads Córtex

Inteligência de tráfego pago para Claude Code. Diagnóstico, relatório, auditoria e estratégia para Meta Ads e Google Ads com benchmarks do mercado brasileiro.

## Instalação

```bash
git clone https://github.com/LittleBugOld/ads-cortex ~/.claude/skills/ads-cortex
```

## Pré-requisitos

Precisa de pelo menos uma skill de execução instalada:

- **Meta Ads**: `git clone https://github.com/LittleBugOld/meta-ads-cortex ~/.claude/skills/meta-ads-cortex`
- **Google Ads**: em breve
- **GA4**: em breve

## Setup

```
/ads-cortex setup
```

Guia o cadastro de contas e testa conexões.

## Comandos

| Comando | O que faz | Quando usar |
|---|---|---|
| `/ads-cortex setup` | Configura contas e testa conexões | Primeira vez |
| `/ads-cortex diagnostico` | Health Score + KPIs + alertas automáticos | Check diário (5 min) |
| `/ads-cortex relatorio` | Dashboard HTML com benchmarks BR | Entrega pro cliente |
| `/ads-cortex auditoria` | Análise profunda com Quality Gates | Revisão mensal |

## O que está incluso

- **Benchmarks BR**: métricas de referência do mercado brasileiro por nicho
- **Quality Gates**: regras de decisão (3x Kill Rule, limites de escala, bidding)
- **Health Score**: nota 0-100 da conta com classificação A-F
- **Alertas automáticos**: detecção de problemas com números e ações

## Arquitetura

```
ads-cortex (cérebro — estratégia + inteligência)
  ├── referencia → meta-ads-cortex (execução Meta)
  ├── referencia → google-ads-cortex (execução Google)
  └── referencia → ga4-cortex (execução Analytics)
```

## Licença e proveniência

Open source sob **MIT** (ver [LICENSE](LICENSE)). Gratuito: o valor está na
implementação, não no código. Inspirado no projeto **Ratos de IA**
(ratosdeia.com.br) e atualizado pela comunidade open source. Detalhes em
[NOTICE.md](NOTICE.md).
