---
name: gsc-cortex
description: Consulta Google Search Console via API oficial (google-api-python-client). Lista properties, submete sitemaps, inspeciona URLs (canonical/indexacao/cobertura), gera relatorio de queries/clicks/impressions/CTR/position e monitora 301 redirects. Use quando o usuario mencionar google search console, gsc, search console, indexacao google, sitemap google, queries google, clicks google, impressions, ctr, posicao google, cobertura, url inspection, change of address, migracao seo. Tambem dispara com /gsc-cortex setup.
---

# GSC Córtex

Skill para consulta de dados do Google Search Console via API oficial (`google-api-python-client`). Lista properties, submete sitemaps, inspeciona URLs, gera relatorios de queries/clicks/impressions/CTR/position.

**IMPORTANTE: Change of Address NAO esta disponivel via API.** Eh restrito ao dashboard GSC. Esta skill cobre tudo que API expoe.

**IMPORTANTE: Se ja existe ga4-cortex configurado, podemos reusar OAuth client_id/secret. Refresh token precisa ser gerado de novo com escopo webmasters.**

## Setup (primeira vez)

### 1. Dependencias

```bash
pip3 install google-api-python-client google-auth google-auth-oauthlib
```

### 2. .env

Checar se existe `~/.claude/skills/gsc-cortex/.env`. Se NAO existir, criar:

```
# GSC Córtex
GSC_CLIENT_ID=""
GSC_CLIENT_SECRET=""
GSC_REFRESH_TOKEN=""
# Site default (opcional): "sc-domain:digitale.com.br" ou "https://digitale.com.br/"
GSC_DEFAULT_SITE=""
```

Se `~/.claude/skills/ga4-cortex/.env` existir e tiver `GA4_CLIENT_ID`/`GA4_CLIENT_SECRET`, **reusa** esses valores em `GSC_CLIENT_ID`/`GSC_CLIENT_SECRET`. Mesmo OAuth client.

### 3. Refresh token

```bash
python3 ~/.claude/skills/gsc-cortex/scripts/generate_token.py
```

Abre browser, pede pra autorizar escopo `webmasters` e `webmasters.readonly`. Cola codigo. Salva refresh token no .env.

### 4. Confirma

```bash
python3 ~/.claude/skills/gsc-cortex/scripts/sites.py
```

Deve listar todas properties do usuario.

## Comandos

### Listar properties

```bash
python3 ~/.claude/skills/gsc-cortex/scripts/sites.py
```

### Sitemap

```bash
# Submeter
python3 ~/.claude/skills/gsc-cortex/scripts/sitemap.py submit <SITE> <SITEMAP_URL>

# Listar status
python3 ~/.claude/skills/gsc-cortex/scripts/sitemap.py list <SITE>

# Detalhe
python3 ~/.claude/skills/gsc-cortex/scripts/sitemap.py status <SITE> <SITEMAP_URL>
```

Onde `<SITE>` eh `sc-domain:digitale.com.br` (Domain property) ou `https://digitale.com.br/` (URL prefix property).

### URL inspection

```bash
python3 ~/.claude/skills/gsc-cortex/scripts/url_inspect.py <SITE> <URL>
```

Retorna: status de cobertura, canonical declarado vs Google, ultima crawled date, sitemaps que apontam, indexacao status, mobile usability.

### Search analytics

```bash
# Top queries dos ultimos 28 dias
python3 ~/.claude/skills/gsc-cortex/scripts/search.py queries <SITE>

# Top pages
python3 ~/.claude/skills/gsc-cortex/scripts/search.py pages <SITE>

# Range custom
python3 ~/.claude/skills/gsc-cortex/scripts/search.py queries <SITE> --start 2026-04-01 --end 2026-04-30 --rows 50
```

## Casos de uso

- **Migracao SEO** (subdomain -> path): verificar se Google indexou URLs novas, se canonical bate, status de cobertura
- **Diagnostico mensal**: queries que mais clicam, posicao media, CTR, paginas em queda
- **Sitemap monitoring**: confirmar que sitemap.xml processou sem erros
- **URL inspection** apos publicar artigo: confirmar indexacao
- **Relatorio cliente**: dados de busca organica integrados com GA4

## Properties Digitale

- `https://digitale.com.br/` (URL prefix, recomendado registrar tambem `sc-domain:digitale.com.br`)
- `https://blog.digitale.com.br/` (subdomain antigo, manter 6+ meses pos-migracao)

## NAO use

- Change of Address: dashboard manual
- Adicionar property nova: dashboard manual
- Verificar property: dashboard manual (TXT DNS ou meta tag)
- Solicitar reindexacao em massa: GSC limita
