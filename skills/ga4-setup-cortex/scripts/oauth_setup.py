#!/usr/bin/env python3
"""GA4 Setup - OAuth setup. Roda uma vez pra gerar refresh_token com escopos Analytics Admin.

ATENÇÃO: Este token é SEPARADO do gtm-cortex. O token do GTM não cobre
analytics.edit nem analytics.manage.users — precisa gerar aqui mesmo.

Pré-requisito:
    - Analytics Admin API habilitada no Google Cloud Console
    - GA4C_CLIENT_ID e GA4C_CLIENT_SECRET preenchidos no .env

Uso:
    python3 oauth_setup.py
"""
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = SKILL_DIR / ".env"

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERRO: google-auth-oauthlib não instalado.", file=sys.stderr)
    print("Rode: pip3 install --user google-auth-oauthlib", file=sys.stderr)
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.manage.users",
]


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


def write_env(env):
    lines = [
        "# GA4 Setup - OAuth user-flow",
        "# Reusa CLIENT_ID e CLIENT_SECRET do gtm-cortex (mesmo OAuth client Google).",
        "# GA4C_REFRESH_TOKEN é DIFERENTE do GTM_REFRESH_TOKEN — escopos distintos.",
        "# Gerar rodando: python3 scripts/oauth_setup.py",
        "# IMPORTANTE: este .env está no .gitignore. NUNCA commitar.",
        "",
        f'GA4C_CLIENT_ID="{env["GA4C_CLIENT_ID"]}"',
        f'GA4C_CLIENT_SECRET="{env["GA4C_CLIENT_SECRET"]}"',
        f'GA4C_REFRESH_TOKEN="{env["GA4C_REFRESH_TOKEN"]}"',
        "",
    ]
    ENV_PATH.write_text("\n".join(lines))


def main():
    env = load_env()
    if not env.get("GA4C_CLIENT_ID") or not env.get("GA4C_CLIENT_SECRET"):
        print(f"ERRO: GA4C_CLIENT_ID e GA4C_CLIENT_SECRET precisam estar no .env", file=sys.stderr)
        print(f"  Arquivo: {ENV_PATH}", file=sys.stderr)
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": env["GA4C_CLIENT_ID"],
            "client_secret": env["GA4C_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    print("\n=== OAuth GA4 Setup ===")
    print("Escopos solicitados:")
    for s in SCOPES:
        print(f"  - {s}")
    print()
    print("Vai abrir browser. Loga com a conta Google que tem acesso ao GA4.")
    print("ATENÇÃO: esses escopos são DIFERENTES do GTM — token separado obrigatório.\n")

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        access_type="offline",
        success_message="Autorizado. Pode fechar essa aba.",
    )

    if not creds.refresh_token:
        print("\nERRO: não recebeu refresh_token.", file=sys.stderr)
        print("Possíveis causas:", file=sys.stderr)
        print("  1. Analytics Admin API não está habilitada no Google Cloud", file=sys.stderr)
        print("     → https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com", file=sys.stderr)
        print("  2. Conta Google sem acesso a nenhuma propriedade GA4", file=sys.stderr)
        sys.exit(1)

    env["GA4C_REFRESH_TOKEN"] = creds.refresh_token
    write_env(env)
    print(f"\n✓ refresh_token salvo em {ENV_PATH}")
    print("\nPróximo passo:")
    print("  python3 create_property.py accounts")


if __name__ == "__main__":
    main()
