"""OAuth helper para GSC. Reusa .env do skill."""
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ENV_PATH = Path.home() / ".claude/skills/gsc-cortex/.env"
SCOPES = ["https://www.googleapis.com/auth/webmasters"]


def load_env():
    if not ENV_PATH.exists():
        raise SystemExit(f"Falta .env em {ENV_PATH}. Rodar /gsc-cortex setup.")
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def save_env(updates: dict):
    env = load_env() if ENV_PATH.exists() else {}
    env.update(updates)
    lines = ["# GSC Córtex config"]
    for k, v in env.items():
        lines.append(f'{k}="{v}"')
    ENV_PATH.write_text("\n".join(lines) + "\n")


def get_service():
    env = load_env()
    cid = env.get("GSC_CLIENT_ID")
    csec = env.get("GSC_CLIENT_SECRET")
    rt = env.get("GSC_REFRESH_TOKEN")
    if not (cid and csec and rt):
        raise SystemExit("GSC_CLIENT_ID/SECRET/REFRESH_TOKEN ausentes no .env. Rodar generate_token.py.")
    creds = Credentials(
        token=None,
        refresh_token=rt,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cid,
        client_secret=csec,
        scopes=SCOPES,
    )
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)
