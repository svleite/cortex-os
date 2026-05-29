#!/usr/bin/env python3
"""GTM Manager - OAuth setup. Roda uma vez pra gerar refresh_token.

Abre browser, você autoriza com sua conta Google, e o script salva
o refresh_token no .env automaticamente.

Uso:
    python3 oauth_setup.py
"""
import json
import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = SKILL_DIR / ".env"

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/tagmanager.readonly",
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/tagmanager.edit.containerversions",
    "https://www.googleapis.com/auth/tagmanager.publish",
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
        "# GTM Manager - OAuth user-flow",
        "# IMPORTANTE: este .env está no .gitignore. NUNCA commitar.",
        "",
        f'GTM_CLIENT_ID="{env["GTM_CLIENT_ID"]}"',
        f'GTM_CLIENT_SECRET="{env["GTM_CLIENT_SECRET"]}"',
        f'GTM_REFRESH_TOKEN="{env["GTM_REFRESH_TOKEN"]}"',
        "",
    ]
    ENV_PATH.write_text("\n".join(lines))


def main():
    env = load_env()
    if not env.get("GTM_CLIENT_ID") or not env.get("GTM_CLIENT_SECRET"):
        print("ERRO: GTM_CLIENT_ID e GTM_CLIENT_SECRET precisam estar no .env", file=sys.stderr)
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": env["GTM_CLIENT_ID"],
            "client_secret": env["GTM_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    print("\n=== OAuth GTM Manager ===")
    print("Vai abrir browser. Autoriza com a sua conta Google que tem acesso ao GTM container.")
    print("Aceita TODOS os escopos pedidos (Tag Manager).\n")

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        access_type="offline",
        success_message="Autorizado. Pode fechar essa aba.",
    )

    if not creds.refresh_token:
        print("ERRO: não recebeu refresh_token. Tenta de novo.", file=sys.stderr)
        sys.exit(1)

    env["GTM_REFRESH_TOKEN"] = creds.refresh_token
    write_env(env)
    print(f"\n✓ refresh_token salvo em {ENV_PATH}")
    print("Agora roda: python3 auth.py")


if __name__ == "__main__":
    main()
