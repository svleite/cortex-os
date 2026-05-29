#!/usr/bin/env python3
"""GTM Manager - autenticação OAuth user-flow + lista accounts/containers/workspaces.

Pré-requisito: ter rodado `oauth_setup.py` uma vez (gera refresh_token).

Uso:
    python3 auth.py                  # lista tudo acessível
    python3 auth.py --container GTM-XXXXXXXX  # detalha um container específico
"""
import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = SKILL_DIR / ".env"

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERRO: pacotes google-api-python-client e google-auth não instalados.", file=sys.stderr)
    print("Rode: pip3 install --user google-api-python-client google-auth google-auth-oauthlib", file=sys.stderr)
    sys.exit(1)


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


def get_service():
    env = load_env()
    if not env.get("GTM_REFRESH_TOKEN"):
        print(f"ERRO: GTM_REFRESH_TOKEN vazio em {ENV_PATH}", file=sys.stderr)
        print("Rode primeiro: python3 oauth_setup.py", file=sys.stderr)
        sys.exit(1)

    creds = Credentials(
        token=None,
        refresh_token=env["GTM_REFRESH_TOKEN"],
        client_id=env["GTM_CLIENT_ID"],
        client_secret=env["GTM_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("tagmanager", "v2", credentials=creds, cache_discovery=False)


def list_all(service):
    accounts = service.accounts().list().execute().get("account", [])
    if not accounts:
        print("Nenhum account acessível pra esta conta Google.", file=sys.stderr)
        return
    for acc in accounts:
        print(f"\n## Account: {acc['name']} (id={acc['accountId']}, path={acc['path']})")
        containers = service.accounts().containers().list(parent=acc["path"]).execute().get("container", [])
        for c in containers:
            print(f"  - Container: {c['name']} (publicId={c['publicId']}, path={c['path']})")
            wss = service.accounts().containers().workspaces().list(parent=c["path"]).execute().get("workspace", [])
            for w in wss:
                print(f"      workspace: {w['name']} (workspaceId={w['workspaceId']}, path={w['path']})")


def find_container(service, public_id):
    accounts = service.accounts().list().execute().get("account", [])
    for acc in accounts:
        containers = service.accounts().containers().list(parent=acc["path"]).execute().get("container", [])
        for c in containers:
            if c["publicId"] == public_id:
                return c
    return None


def detail_container(service, public_id):
    c = find_container(service, public_id)
    if not c:
        print(f"Container {public_id} não encontrado nos accounts acessíveis.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(c, indent=2, ensure_ascii=False))
    wss = service.accounts().containers().workspaces().list(parent=c["path"]).execute().get("workspace", [])
    print("\n## Workspaces:")
    for w in wss:
        print(f"  {w['name']}  (id={w['workspaceId']}, path={w['path']})")
        tags = service.accounts().containers().workspaces().tags().list(parent=w["path"]).execute().get("tag", [])
        triggers = service.accounts().containers().workspaces().triggers().list(parent=w["path"]).execute().get("trigger", [])
        print(f"    tags: {len(tags)}, triggers: {len(triggers)}")
        for t in tags:
            print(f"      tag: [{t.get('type')}] {t.get('name')}")
        for tr in triggers:
            print(f"      trigger: [{tr.get('type')}] {tr.get('name')}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--container", help="Public ID do container (ex: GTM-XXXXXXXX)")
    args = p.parse_args()

    service = get_service()
    if args.container:
        detail_container(service, args.container)
    else:
        list_all(service)


if __name__ == "__main__":
    main()
