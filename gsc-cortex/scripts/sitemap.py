#!/usr/bin/env python3
"""Sitemap GSC: submit, list, status."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.auth import get_service


def cmd_submit(svc, site, sitemap):
    svc.sitemaps().submit(siteUrl=site, feedpath=sitemap).execute()
    print(f"✅ Sitemap submetido: {sitemap}")


def cmd_list(svc, site):
    resp = svc.sitemaps().list(siteUrl=site).execute()
    sm = resp.get("sitemap", [])
    if not sm:
        print("Nenhum sitemap.")
        return
    print(f"{len(sm)} sitemaps em {site}:\n")
    for s in sm:
        path = s.get("path", "")
        last = s.get("lastSubmitted", "")
        last_dl = s.get("lastDownloaded", "")
        warnings = s.get("warnings", 0)
        errors = s.get("errors", 0)
        is_pending = s.get("isPending", False)
        is_sitemap_index = s.get("isSitemapsIndex", False)
        status = "⏳ pending" if is_pending else ("⚠️ erro" if errors else "✅")
        print(f"  {status} {path}")
        print(f"     submetido: {last} | crawled: {last_dl}")
        print(f"     warnings: {warnings} | errors: {errors}{' | INDEX' if is_sitemap_index else ''}")
        contents = s.get("contents", [])
        for c in contents:
            t = c.get("type", "")
            sub = c.get("submitted", "0")
            idx = c.get("indexed", "0")
            print(f"     [{t}] submetidos: {sub} | indexados: {idx}")
        print()


def cmd_status(svc, site, sitemap):
    s = svc.sitemaps().get(siteUrl=site, feedpath=sitemap).execute()
    import json
    print(json.dumps(s, indent=2))


def main():
    if len(sys.argv) < 3:
        print("Uso: sitemap.py {submit|list|status} <SITE> [<SITEMAP_URL>]")
        sys.exit(1)
    action = sys.argv[1]
    site = sys.argv[2]
    svc = get_service()
    if action == "submit":
        cmd_submit(svc, site, sys.argv[3])
    elif action == "list":
        cmd_list(svc, site)
    elif action == "status":
        cmd_status(svc, site, sys.argv[3])
    else:
        print(f"Acao desconhecida: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
