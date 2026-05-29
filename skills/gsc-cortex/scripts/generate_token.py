#!/usr/bin/env python3
"""Gera refresh token OAuth pra GSC. Reusa GA4 client se existir."""
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from lib.auth import ENV_PATH, save_env, load_env, SCOPES


def main():
    env = load_env() if ENV_PATH.exists() else {}
    cid = env.get("GSC_CLIENT_ID")
    csec = env.get("GSC_CLIENT_SECRET")

    if not (cid and csec):
        ga4_env = Path.home() / ".claude/skills/ga4-cortex/.env"
        if ga4_env.exists():
            for line in ga4_env.read_text().splitlines():
                if line.startswith("GA4_CLIENT_ID="):
                    cid = line.split("=", 1)[1].strip().strip('"')
                if line.startswith("GA4_CLIENT_SECRET="):
                    csec = line.split("=", 1)[1].strip().strip('"')

    if not (cid and csec):
        print("Sem GSC_CLIENT_ID/SECRET. Cole agora:")
        cid = input("Client ID: ").strip()
        csec = input("Client Secret: ").strip()

    client_config = {
        "installed": {
            "client_id": cid,
            "client_secret": csec,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    save_env({
        "GSC_CLIENT_ID": cid,
        "GSC_CLIENT_SECRET": csec,
        "GSC_REFRESH_TOKEN": creds.refresh_token,
    })
    print(f"\n✅ Refresh token salvo em {ENV_PATH}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
