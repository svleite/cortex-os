#!/usr/bin/env python3
"""Biblioteca comum do gtm-cortex: OAuth (refresh token), chamadas REST e resolução de container.

Só biblioteca padrão do Python 3.9+. Nenhum ID de cliente fica gravado no código:
o container é resolvido pelo ID público (GTM-XXXX) via API, na hora.

Credenciais (.env com GTM_CLIENT_ID, GTM_CLIENT_SECRET, GTM_REFRESH_TOKEN), nesta ordem:
  1. variável de ambiente GTM_CORTEX_ENV (caminho do arquivo)
  2. .env da própria skill
  3. ~/.claude/skills/gtm-cortex/.env (instalação padrão)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://tagmanager.googleapis.com/tagmanager/v2"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SKILL_DIR = Path(__file__).resolve().parent.parent

# Gatilhos nativos do GTM (IDs fixos da plataforma)
ALL_PAGES = "2147479553"
INITIALIZATION = "2147479573"

_token_cache = {}


class GTMError(Exception):
    pass


def _env_path():
    cands = [os.environ.get("GTM_CORTEX_ENV"), SKILL_DIR / ".env",
             Path.home() / ".claude/skills/gtm-cortex/.env"]
    for c in cands:
        if c and Path(c).is_file():
            return Path(c)
    raise GTMError("Sem .env do gtm-cortex. Rode oauth_setup.py (ver SKILL.md, Setup).")


def load_env():
    env = {}
    for line in _env_path().read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    falta = [k for k in ("GTM_CLIENT_ID", "GTM_CLIENT_SECRET", "GTM_REFRESH_TOKEN") if not env.get(k)]
    if falta:
        raise GTMError("Faltam no .env: " + ", ".join(falta))
    return env


def token():
    if _token_cache.get("exp", 0) > time.time() + 60:
        return _token_cache["tok"]
    env = load_env()
    data = urllib.parse.urlencode({
        "client_id": env["GTM_CLIENT_ID"],
        "client_secret": env["GTM_CLIENT_SECRET"],
        "refresh_token": env["GTM_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data), timeout=30) as r:
            j = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise GTMError(f"OAuth falhou (HTTP {e.code}). Refresh token revogado? Rode oauth_setup.py.") from None
    _token_cache.update(tok=j["access_token"], exp=time.time() + int(j.get("expires_in", 3000)))
    return _token_cache["tok"]


def call(method, path, body=None, query=None):
    url = API + path + ("?" + urllib.parse.urlencode(query, doseq=True) if query else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token())
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            corpo = e.read().decode("utf-8", "ignore")
            if e.code == 429 and tentativa < 2:  # cota por minuto da API do GTM
                time.sleep(15 * (tentativa + 1))
                continue
            raise GTMError(f"{method} {path} -> HTTP {e.code}: {corpo[:400]}") from None


def resolve_container(public_id):
    """GTM-XXXX -> dict(account, container, public_id, name, path)."""
    public_id = public_id.strip().upper()
    for acc in call("GET", "/accounts").get("account", []):
        for c in call("GET", f"/accounts/{acc['accountId']}/containers").get("container", []):
            if c.get("publicId", "").upper() == public_id:
                return dict(account=acc["accountId"], container=c["containerId"], public_id=public_id,
                            name=c.get("name", ""), path=c["path"])
    raise GTMError(f"Container {public_id} não encontrado nas contas acessíveis por este login.")


def workspace(ctr, nome=None):
    """Devolve o workspace pelo nome (padrão: Default Workspace, senão o primeiro)."""
    wss = call("GET", f"/{ctr['path']}/workspaces").get("workspace", [])
    alvo = nome or "Default Workspace"
    for w in wss:
        if w.get("name") == alvo:
            return w
    if nome:
        raise GTMError(f"Workspace '{nome}' não existe em {ctr['public_id']}. Existentes: {[w['name'] for w in wss]}")
    if not wss:
        raise GTMError("Container sem workspace.")
    return wss[0]


def listar(ws_path, tipo):
    """tipo: tags | triggers | variables | built_in_variables"""
    chave = {"tags": "tag", "triggers": "trigger", "variables": "variable",
             "built_in_variables": "builtInVariable"}[tipo]
    return call("GET", f"/{ws_path}/{tipo}").get(chave, [])


def p(key, value, tipo="template"):
    """Parâmetro simples do GTM."""
    return {"type": tipo, "key": key, "value": str(value)}


def saida(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main_seguro(fn):
    try:
        fn()
    except GTMError as e:
        saida({"erro": str(e)})
        sys.exit(1)
