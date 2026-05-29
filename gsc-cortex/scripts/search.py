#!/usr/bin/env python3
"""Search analytics: queries, pages."""
import sys
import argparse
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.auth import get_service


def fmt(n):
    if isinstance(n, float):
        return f"{n:.2f}"
    return str(n)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("dim", choices=["queries", "pages", "country", "device"])
    p.add_argument("site")
    p.add_argument("--start", default=(date.today() - timedelta(days=28)).isoformat())
    p.add_argument("--end", default=date.today().isoformat())
    p.add_argument("--rows", type=int, default=25)
    args = p.parse_args()

    dim_map = {"queries": "query", "pages": "page", "country": "country", "device": "device"}
    svc = get_service()
    body = {
        "startDate": args.start,
        "endDate": args.end,
        "dimensions": [dim_map[args.dim]],
        "rowLimit": args.rows,
    }
    resp = svc.searchanalytics().query(siteUrl=args.site, body=body).execute()
    rows = resp.get("rows", [])
    if not rows:
        print("Sem dados no periodo.")
        return

    print(f"\n{args.site} | {args.start} a {args.end} | {args.dim.upper()}\n")
    print(f"{'#':<4} {'KEY':<60} {'CLICKS':>8} {'IMPR':>8} {'CTR':>7} {'POS':>6}")
    print("-" * 100)
    for i, r in enumerate(rows, 1):
        k = r["keys"][0]
        if len(k) > 58:
            k = k[:55] + "..."
        print(f"{i:<4} {k:<60} {fmt(int(r['clicks'])):>8} {fmt(int(r['impressions'])):>8} {fmt(r['ctr']*100)+'%':>7} {fmt(r['position']):>6}")

    tot_c = sum(int(r["clicks"]) for r in rows)
    tot_i = sum(int(r["impressions"]) for r in rows)
    print("-" * 100)
    print(f"TOTAL ({len(rows)} linhas): clicks {tot_c} | impressions {tot_i}")


if __name__ == "__main__":
    main()
