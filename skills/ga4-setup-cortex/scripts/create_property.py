#!/usr/bin/env python3
"""GA4 Setup - cria propriedade GA4 e fluxo de dados web via Analytics Admin API.

Retorna Measurement ID (G-XXXXXXXXXX) e atualiza cliente.md opcionalmente.

Uso:
    python3 create_property.py accounts
        Lista contas GA4 acessíveis (pegar o account_id aqui)

    python3 create_property.py create \\
        --name "Nome do Cliente" \\
        --url "https://www.seusite.com.br" \\
        --account-id "123456789" \\
        [--timezone "America/Sao_Paulo"] \\
        [--currency BRL] \\
        [--client-slug "slug-do-cliente"]
        Cria propriedade + web data stream. Se --client-slug, atualiza cliente.md.
"""
import argparse
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = SKILL_DIR / ".env"

# Caminho até a raiz do projeto (onde fica a pasta clientes/):
# create_property.py -> scripts/ -> ga4-setup-cortex/ -> skills/ -> .claude/ -> projeto/
PROJECT_ROOT = Path(__file__).resolve().parents[4]

try:
    from google.oauth2.credentials import Credentials
    from google.analytics import admin as ga_admin
except ImportError:
    print("ERRO: pacote google-analytics-admin não instalado.", file=sys.stderr)
    print("Rode: pip3 install google-analytics-admin google-auth", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def load_env():
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_client():
    env = load_env()
    if not env.get("GA4C_REFRESH_TOKEN"):
        print(f"ERRO: GA4C_REFRESH_TOKEN vazio em {ENV_PATH}", file=sys.stderr)
        print("Rode primeiro: python3 oauth_setup.py", file=sys.stderr)
        sys.exit(1)

    creds = Credentials(
        token=None,
        refresh_token=env["GA4C_REFRESH_TOKEN"],
        client_id=env["GA4C_CLIENT_ID"],
        client_secret=env["GA4C_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=[
            "https://www.googleapis.com/auth/analytics.edit",
            "https://www.googleapis.com/auth/analytics.manage.users",
        ],
    )
    return ga_admin.AnalyticsAdminServiceClient(credentials=creds)


# ---------------------------------------------------------------------------
# Subcomandos
# ---------------------------------------------------------------------------

def cmd_accounts(client):
    print("\n=== Contas GA4 acessíveis ===")
    try:
        accounts = list(client.list_accounts())
    except Exception as e:
        print(f"ERRO ao listar contas: {e}", file=sys.stderr)
        sys.exit(1)

    if not accounts:
        print("Nenhuma conta GA4 acessível pra esta conta Google.")
        print("Verifica se a conta Google tem acesso ao Google Analytics.")
        return

    for acc in accounts:
        account_id = acc.name.split("/")[-1]
        print(f"  - {acc.display_name}  (account_id={account_id})")

    print(f"\nTotal: {len(accounts)} conta(s)")
    print("\nUse o account_id no comando 'create --account-id'.")


def cmd_create(client, args):
    parent = f"accounts/{args.account_id}"

    print(f"\nCriando propriedade '{args.name}'...")
    print(f"  Conta: {parent}")
    print(f"  URL:   {args.url}")
    print(f"  Fuso:  {args.timezone}")
    print(f"  Moeda: {args.currency}")

    try:
        prop = client.create_property(
            property=ga_admin.Property(
                display_name=args.name,
                time_zone=args.timezone,
                currency_code=args.currency,
                parent=parent,
            )
        )
    except Exception as e:
        print(f"\nERRO ao criar propriedade: {e}", file=sys.stderr)
        _hint_error(str(e))
        sys.exit(1)

    prop_id = prop.name.split("/")[-1]
    print(f"\n  Propriedade criada: {prop.name}")

    print(f"\nCriando web data stream para {args.url}...")
    try:
        stream = client.create_data_stream(
            parent=prop.name,
            data_stream=ga_admin.DataStream(
                type_=ga_admin.DataStream.DataStreamType.WEB_DATA_STREAM,
                display_name=args.name,
                web_stream_data=ga_admin.DataStream.WebStreamData(
                    default_uri=args.url,
                ),
            ),
        )
    except Exception as e:
        print(f"\nERRO ao criar data stream: {e}", file=sys.stderr)
        print(f"  Propriedade foi criada ({prop.name}) mas o stream falhou.", file=sys.stderr)
        print(f"  Cria o stream manualmente em analytics.google.com ou tenta de novo.", file=sys.stderr)
        sys.exit(1)

    measurement_id = stream.web_stream_data.measurement_id

    print(f"\n{'='*52}")
    print(f"  Measurement ID : {measurement_id}")
    print(f"  Property ID    : {prop_id}")
    print(f"  Property name  : {prop.name}")
    print(f"  Stream         : {stream.name}")
    print(f"{'='*52}")
    print(f"\nSnippet pra colocar no GTM:")
    print(f"  Measurement ID: {measurement_id}")

    if args.client_slug:
        update_cliente_md(args.client_slug, measurement_id)

    return measurement_id


def _hint_error(msg: str):
    if "PERMISSION_DENIED" in msg or "403" in msg:
        print("  → Conta Google sem permissão pra criar propriedades nessa conta GA4.", file=sys.stderr)
        print("    Verifica se o usuário é admin da conta em analytics.google.com/admin.", file=sys.stderr)
    elif "UNAUTHENTICATED" in msg or "401" in msg:
        print("  → Token expirado ou inválido. Rode: python3 oauth_setup.py", file=sys.stderr)
    elif "NOT_FOUND" in msg or "404" in msg:
        print("  → account_id não encontrado. Confirma com: python3 create_property.py accounts", file=sys.stderr)


# ---------------------------------------------------------------------------
# Atualizar cliente.md
# ---------------------------------------------------------------------------

def update_cliente_md(slug: str, measurement_id: str):
    md_path = PROJECT_ROOT / "clientes" / slug / "cliente.md"

    if not md_path.exists():
        print(f"\nAVISO: cliente.md não encontrado em {md_path}", file=sys.stderr)
        print(f"  Adicione manualmente: - **GA4:** `{measurement_id}`", file=sys.stderr)
        return

    content = md_path.read_text()
    new_line = f"- **GA4:** `{measurement_id}`"

    # Padrões comuns no cliente.md (do mais específico pro mais genérico)
    patterns = [
        r"- \[ \] Google Analytics / GA4[^\n]*",
        r"- \[ \] GA4 \(criar\)[^\n]*",
        r"- \[ \] GA4[^\n]*",
        r"- \[x\] GA4[^\n]*",
    ]

    updated = content
    matched = False
    for pattern in patterns:
        if re.search(pattern, updated):
            updated = re.sub(pattern, new_line, updated, count=1)
            matched = True
            break

    if not matched:
        print(f"\nAVISO: nenhum campo GA4 encontrado em {md_path}", file=sys.stderr)
        print(f"  Adicione manualmente: {new_line}", file=sys.stderr)
        return

    md_path.write_text(updated)
    print(f"\n  cliente.md atualizado: clientes/{slug}/cliente.md")
    print(f"  Linha: {new_line}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="GA4 Setup - cria propriedades GA4 via Analytics Admin API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # accounts
    sub.add_parser("accounts", help="Lista contas GA4 acessíveis")

    # create
    c = sub.add_parser("create", help="Cria propriedade + web data stream")
    c.add_argument("--name", required=True,
                   help="Nome da propriedade (ex: 'Nome do Cliente')")
    c.add_argument("--url", required=True,
                   help="URL do site (ex: 'https://www.seusite.com.br')")
    c.add_argument("--account-id", required=True,
                   help="ID da conta GA4 — obter via 'accounts'")
    c.add_argument("--timezone", default="America/Sao_Paulo",
                   help="Fuso horário (padrão: America/Sao_Paulo)")
    c.add_argument("--currency", default="BRL",
                   help="Código de moeda ISO 4217 (padrão: BRL)")
    c.add_argument("--client-slug",
                   help="Slug do cliente pra atualizar clientes/[slug]/cliente.md")

    args = p.parse_args()
    client = get_client()

    if args.cmd == "accounts":
        cmd_accounts(client)
    elif args.cmd == "create":
        cmd_create(client, args)


if __name__ == "__main__":
    main()
