# GA4 Córtex

Skill do ecossistema Córtex para consulta de dados do Google Analytics 4 via SDK oficial (`google-analytics-data`).

## O que faz

- Consulta propriedades e detalhes de conta GA4
- Gera relatórios de sessões, usuários, pageviews, bounce rate, conversões
- Analisa fontes de tráfego (source/medium), landing pages, campanhas UTM
- Breakdown por dispositivo e geolocalização
- Dados em tempo real (usuários ativos, páginas, eventos)
- Query customizada com métricas e dimensões livres

## Pré-requisitos

```bash
pip3 install google-analytics-data google-auth
```

## Configuração

Crie o arquivo `~/.claude/skills/ga4-cortex/.env`:

```
GA4_PROPERTY_ID="123456789"

# Opção 1: Service Account
GA4_CREDENTIALS_PATH="/path/to/service-account.json"

# Opção 2: OAuth2 (compartilhado com google-ads-cortex)
# Deixe GA4_CREDENTIALS_PATH vazio: busca automaticamente do google-ads-cortex
```

## Uso

```bash
# Resumo geral dos últimos 30 dias
python3 scripts/reports.py overview --date-range 30daysAgo

# Fontes de tráfego
python3 scripts/reports.py traffic-sources --date-range 7daysAgo

# Dados em tempo real
python3 scripts/realtime.py now
```

## Ecossistema Córtex

- **meta-ads-cortex**: Gestão de Meta Ads (Facebook/Instagram)
- **google-ads-cortex**: Gestão de Google Ads
- **ga4-cortex**: Consulta de dados GA4 (este)
- **ads-cortex**: Camada de inteligência (diagnóstico, auditoria, estratégia)

## Licença e proveniência

Open source sob **MIT** (ver [LICENSE](LICENSE)). Gratuito: o valor está na
implementação, não no código. Inspirado no projeto **Ratos de IA**
(ratosdeia.com.br) e atualizado pela comunidade open source. Detalhes em
[NOTICE.md](NOTICE.md).
