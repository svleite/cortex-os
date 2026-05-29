#!/usr/bin/env python3
"""Lista properties GSC do usuario."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.auth import get_service


def main():
    svc = get_service()
    resp = svc.sites().list().execute()
    sites = resp.get("siteEntry", [])
    if not sites:
        print("Nenhuma property encontrada.")
        return
    print(f"{len(sites)} properties:\n")
    for s in sites:
        url = s.get("siteUrl", "")
        perm = s.get("permissionLevel", "")
        print(f"  {url:<45} [{perm}]")


if __name__ == "__main__":
    main()
