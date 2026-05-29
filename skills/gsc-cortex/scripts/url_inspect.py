#!/usr/bin/env python3
"""URL inspection: indexacao, canonical, cobertura."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.auth import get_service


def main():
    if len(sys.argv) < 3:
        print("Uso: inspect.py <SITE> <URL>")
        sys.exit(1)
    site = sys.argv[1]
    url = sys.argv[2]
    svc = get_service()
    body = {"inspectionUrl": url, "siteUrl": site, "languageCode": "pt-BR"}
    resp = svc.urlInspection().index().inspect(body=body).execute()
    r = resp.get("inspectionResult", {})
    idx = r.get("indexStatusResult", {})

    print(f"URL: {url}")
    print(f"Site: {site}")
    print()
    print(f"Verdict:           {idx.get('verdict', '?')}")
    print(f"Cobertura:         {idx.get('coverageState', '?')}")
    print(f"Indexacao:         {idx.get('indexingState', '?')}")
    print(f"Crawl ultimo:      {idx.get('lastCrawlTime', '-')}")
    print(f"Robots.txt:        {idx.get('robotsTxtState', '?')}")
    print(f"Pode ser indexado: {idx.get('pageFetchState', '?')}")
    print()
    print(f"Canonical Google:  {idx.get('googleCanonical', '-')}")
    print(f"Canonical declarado: {idx.get('userCanonical', '-')}")
    print(f"Crawled As:        {idx.get('crawledAs', '-')}")
    print()
    sitemaps = idx.get("sitemap", [])
    print(f"Sitemaps que listam: {sitemaps if sitemaps else '(nenhum)'}")
    referring = idx.get("referringUrls", [])
    if referring:
        print(f"Referring URLs: {len(referring)}")
        for r2 in referring[:5]:
            print(f"  - {r2}")

    mob = r.get("mobileUsabilityResult", {})
    if mob:
        print(f"\nMobile: {mob.get('verdict', '?')}")
        for issue in mob.get("issues", []):
            print(f"  ⚠️ {issue.get('issueType')} | {issue.get('message')}")

    rich = r.get("richResultsResult", {})
    if rich:
        print(f"\nRich results: {rich.get('verdict', '?')}")

    if "--json" in sys.argv:
        print("\n--- raw JSON ---")
        print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
