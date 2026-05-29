#!/usr/bin/env python3
"""
RD Station Córtex — Read operations
CLI for reading RD Station Marketing data via API v2 (OAuth2).
Subcommands: auth, accounts, leads, funnel, conversions, summary
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
import yaml
from dotenv import load_dotenv, set_key

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SKILL_DIR = Path(__file__).parent.parent
ENV_FILE = SKILL_DIR / ".env"
CONTAS_FILE = SKILL_DIR / "contas.yaml"

load_dotenv(ENV_FILE)

API_BASE = "https://api.rd.services/platform"
TOKEN_URL = "https://api.rd.services/auth/token"
AUTH_URL = "https://api.rd.services/auth/dialog"

# Active credentials for current command (set by main before dispatch)
_CREDS = {"client_id": None, "client_secret": None, "access_token": None, "refresh_token": None}


# ---------------------------------------------------------------------------
# OAuth2 helpers
# ---------------------------------------------------------------------------

def _load_env_creds():
    load_dotenv(ENV_FILE, override=True)
    return {
        "client_id": os.getenv("RD_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("RD_CLIENT_SECRET", "").strip(),
        "access_token": os.getenv("RD_ACCESS_TOKEN", "").strip(),
        "refresh_token": os.getenv("RD_REFRESH_TOKEN", "").strip(),
    }


def _save_tokens(access_token, refresh_token):
    set_key(str(ENV_FILE), "RD_ACCESS_TOKEN", access_token)
    if refresh_token:
        set_key(str(ENV_FILE), "RD_REFRESH_TOKEN", refresh_token)
    _CREDS["access_token"] = access_token
    if refresh_token:
        _CREDS["refresh_token"] = refresh_token


def _do_refresh():
    resp = requests.post(TOKEN_URL, json={
        "client_id": _CREDS["client_id"],
        "client_secret": _CREDS["client_secret"],
        "refresh_token": _CREDS["refresh_token"],
    })
    if not resp.ok:
        print(f"ERRO ao renovar token: {resp.status_code} {resp.text}", file=sys.stderr)
        print("Rodar novamente: read.py auth", file=sys.stderr)
        sys.exit(1)
    data = resp.json()
    _save_tokens(data["access_token"], data.get("refresh_token", _CREDS["refresh_token"]))
    return data["access_token"]


def _init_creds():
    """Load credentials into _CREDS. Exit with helpful message if not configured."""
    creds = _load_env_creds()
    if not creds["client_id"] or not creds["client_secret"]:
        print("ERRO: RD_CLIENT_ID e RD_CLIENT_SECRET não configurados.", file=sys.stderr)
        print("Passos:", file=sys.stderr)
        print("  1. Acessar app.rdstation.com.br/api-credentials", file=sys.stderr)
        print("  2. Criar app → copiar Client ID e Client Secret", file=sys.stderr)
        print("  3. Preencher RD_CLIENT_ID e RD_CLIENT_SECRET em ~/.claude/skills/rd-station-cortex/.env", file=sys.stderr)
        print("  4. Rodar: python3 read.py auth", file=sys.stderr)
        sys.exit(1)
    _CREDS.update(creds)
    if not _CREDS["refresh_token"]:
        print("ERRO: RD_REFRESH_TOKEN não configurado. Rodar: python3 read.py auth", file=sys.stderr)
        sys.exit(1)
    if not _CREDS["access_token"]:
        _do_refresh()


# ---------------------------------------------------------------------------
# API helper
# ---------------------------------------------------------------------------

def _api_get(path, params=None, retry=True):
    """GET with Bearer token, auto-refresh on 401."""
    url = f"{API_BASE}{path}"
    headers = {"Authorization": f"Bearer {_CREDS['access_token']}"}
    resp = requests.get(url, headers=headers, params=params or {})
    if resp.status_code == 401 and retry:
        _do_refresh()
        return _api_get(path, params=params, retry=False)
    if not resp.ok:
        print(f"ERRO {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _default_since():
    return datetime.today().replace(day=1).strftime("%Y-%m-%d")


def _default_until():
    return datetime.today().strftime("%Y-%m-%d")


def _to_iso(date_str):
    return f"{date_str}T00:00:00-03:00" if "T" not in date_str else date_str


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_auth(args):
    """Interactive OAuth2 authorization flow."""
    creds = _load_env_creds()
    client_id = creds["client_id"]
    client_secret = creds["client_secret"]
    if not client_id or not client_secret:
        print("ERRO: Preencher RD_CLIENT_ID e RD_CLIENT_SECRET no .env antes de rodar auth.", file=sys.stderr)
        sys.exit(1)

    redirect_uri = "https://app.rdstation.com.br/oauth-callback"
    auth_link = f"{AUTH_URL}?{urlencode({'client_id': client_id, 'redirect_uri': redirect_uri, 'response_type': 'code'})}"

    print(f"\n1. Acessar esta URL no navegador:\n\n   {auth_link}\n")
    print("2. Autorizar o app")
    print("3. Copiar o valor de 'code' da URL de retorno (após ?code=)\n")
    code = input("Cole o code aqui: ").strip()
    if not code:
        print("ERRO: code vazio", file=sys.stderr)
        sys.exit(1)

    resp = requests.post(TOKEN_URL, json={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
    })
    if not resp.ok:
        print(f"ERRO ao trocar code por token: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)
    data = resp.json()
    set_key(str(ENV_FILE), "RD_ACCESS_TOKEN", data["access_token"])
    set_key(str(ENV_FILE), "RD_REFRESH_TOKEN", data["refresh_token"])
    print(f"\n✅ Autorizado! Tokens salvos em {ENV_FILE}")
    print("\nTestar conexão:")
    print("  python3 read.py accounts")


def cmd_accounts(args):
    """Verify token and show contact count."""
    data = _api_get("/contacts", params={"page": 1, "per_page": 1})
    total = data.get("total", "?")
    contacts = data.get("contacts", [])
    print(json.dumps({
        "status": "ok",
        "total_contacts": total,
        "sample": contacts[0] if contacts else None,
    }, indent=2, ensure_ascii=False))


def _fetch_contacts_by_period(since, until, limit=500):
    """Paginate /contacts filtered by creation date."""
    params = {"page": 1, "per_page": 100}
    all_contacts = []
    page = 1
    while len(all_contacts) < limit:
        params["page"] = page
        data = _api_get("/contacts", params=params)
        contacts = data.get("contacts", [])
        if not contacts:
            break
        for c in contacts:
            created = (c.get("created_at") or "")[:10]
            if created < since or created > until:
                continue
            all_contacts.append(c)
        if len(contacts) < 100:
            break
        page += 1
    return all_contacts


def cmd_leads(args):
    """Query leads by UTM origin and date range."""
    since = args.since or _default_since()
    until = args.until or _default_until()
    all_contacts = _fetch_contacts_by_period(since, until, args.limit)

    utm_sources = [s.strip() for s in args.utm_source.split(",")] if args.utm_source else []
    utm_mediums = [m.strip() for m in args.utm_medium.split(",")] if args.utm_medium else []

    if utm_sources:
        all_contacts = [
            c for c in all_contacts
            if any(src.lower() in (c.get("utm_source") or "").lower() for src in utm_sources)
        ]
    if utm_mediums:
        all_contacts = [
            c for c in all_contacts
            if any(med.lower() in (c.get("utm_medium") or "").lower() for med in utm_mediums)
        ]
    if args.utm_campaign:
        all_contacts = [
            c for c in all_contacts
            if args.utm_campaign.lower() in (c.get("utm_campaign") or "").lower()
        ]

    by_source = {}
    for c in all_contacts:
        src = (c.get("utm_source") or "desconhecido").lower()
        by_source.setdefault(src, []).append(c)

    print(json.dumps({
        "periodo": {"since": since, "until": until},
        "total_leads": len(all_contacts),
        "por_origem": {src: len(leads) for src, leads in sorted(by_source.items(), key=lambda x: -len(x[1]))},
        "contatos": [
            {
                "nome": c.get("name", ""),
                "email": c.get("email", ""),
                "utm_source": c.get("utm_source", ""),
                "utm_medium": c.get("utm_medium", ""),
                "utm_campaign": c.get("utm_campaign", ""),
                "created_at": (c.get("created_at") or "")[:10],
                "lifecycle_stage": c.get("lifecycle_stage", ""),
            }
            for c in all_contacts[:50]
        ],
    }, indent=2, ensure_ascii=False))


def cmd_funnel(args):
    """Conversion rates by funnel stage."""
    since = args.since or _default_since()
    until = args.until or _default_until()
    all_contacts = _fetch_contacts_by_period(since, until)
    total = len(all_contacts) or 1

    stages = {"lead": 0, "qualified_lead": 0, "mql": 0, "sql": 0, "opportunity": 0, "customer": 0}
    for c in all_contacts:
        stage = (c.get("lifecycle_stage") or "lead").lower()
        matched = next((k for k in stages if k in stage), None)
        stages[matched or "lead"] += 1

    mql = stages["mql"] + stages["qualified_lead"]
    opportunity = stages["opportunity"] + stages["sql"]
    customer = stages["customer"]

    print(json.dumps({
        "periodo": {"since": since, "until": until},
        "total_leads": total,
        "funil": {
            "lead":          {"total": total,       "taxa": "100%"},
            "mql":           {"total": mql,         "taxa": f"{mql/total*100:.1f}%"},
            "oportunidade":  {"total": opportunity, "taxa": f"{opportunity/total*100:.1f}%"},
            "cliente":       {"total": customer,    "taxa": f"{customer/total*100:.1f}%"},
        },
    }, indent=2, ensure_ascii=False))


def cmd_conversions(args):
    """Conversion events by date."""
    since = args.since or _default_since()
    until = args.until or _default_until()
    all_contacts = _fetch_contacts_by_period(since, until)
    by_day = {}
    for c in all_contacts:
        day = (c.get("created_at") or "")[:10]
        by_day[day] = by_day.get(day, 0) + 1
    print(json.dumps({
        "periodo": {"since": since, "until": until},
        "total_conversoes": len(all_contacts),
        "por_dia": dict(sorted(by_day.items())),
    }, indent=2, ensure_ascii=False))


def cmd_summary(args):
    """Overview: leads, funnel rates, CPL qualified instruction."""
    since = args.since or _default_since()
    until = args.until or _default_until()
    all_contacts = _fetch_contacts_by_period(since, until)
    total = len(all_contacts) or 1

    mql = sum(1 for c in all_contacts if "mql" in (c.get("lifecycle_stage") or "").lower()
              or "qualified" in (c.get("lifecycle_stage") or "").lower())
    opportunity = sum(1 for c in all_contacts if "opportunit" in (c.get("lifecycle_stage") or "").lower()
                      or "sql" in (c.get("lifecycle_stage") or "").lower())
    by_source = {}
    for c in all_contacts:
        src = (c.get("utm_source") or "desconhecido").lower()
        by_source[src] = by_source.get(src, 0) + 1

    print(json.dumps({
        "periodo": {"since": since, "until": until},
        "total_leads": total,
        "mql": mql,
        "taxa_mql": f"{mql/total*100:.1f}%",
        "oportunidades": opportunity,
        "taxa_oportunidade": f"{opportunity/total*100:.1f}%",
        "leads_por_origem": dict(sorted(by_source.items(), key=lambda x: -x[1])),
        "instrucao_cpl_qualificado": (
            "CPL qualificado = gasto por canal (ads) / leads desse canal em oportunidade. "
            "Cruzar 'leads_por_origem' com gastos via google-ads-cortex / meta-ads-cortex."
        ),
    }, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="RD Station Córtex — leitura via API v2 (OAuth2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth", help="Fluxo OAuth2 — rodar uma vez para configurar tokens")

    sub.add_parser("accounts", help="Verifica token e exibe total de contatos")

    p_leads = sub.add_parser("leads", help="Leads por UTM e período")
    p_leads.add_argument("--utm-source", dest="utm_source", help="Origens separadas por vírgula (google,facebook)")
    p_leads.add_argument("--utm-medium", dest="utm_medium", help="Mídias separadas por vírgula")
    p_leads.add_argument("--utm-campaign", dest="utm_campaign", help="Nome da campanha (parcial)")
    p_leads.add_argument("--since", help="Data início YYYY-MM-DD")
    p_leads.add_argument("--until", help="Data fim YYYY-MM-DD")
    p_leads.add_argument("--limit", type=int, default=500)

    p_funnel = sub.add_parser("funnel", help="Taxas de conversão por etapa do funil")
    p_funnel.add_argument("--since", help="Data início YYYY-MM-DD")
    p_funnel.add_argument("--until", help="Data fim YYYY-MM-DD")

    p_conv = sub.add_parser("conversions", help="Conversões por data")
    p_conv.add_argument("--since", help="Data início YYYY-MM-DD")
    p_conv.add_argument("--until", help="Data fim YYYY-MM-DD")

    p_summary = sub.add_parser("summary", help="Visão geral: leads, funil, CPL qualificado")
    p_summary.add_argument("--since", help="Data início YYYY-MM-DD")
    p_summary.add_argument("--until", help="Data fim YYYY-MM-DD")

    args = parser.parse_args()

    if args.cmd != "auth":
        _init_creds()

    {
        "auth": cmd_auth,
        "accounts": cmd_accounts,
        "leads": cmd_leads,
        "funnel": cmd_funnel,
        "conversions": cmd_conversions,
        "summary": cmd_summary,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
