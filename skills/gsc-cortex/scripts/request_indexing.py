#!/usr/bin/env python3
"""
Request Indexing no GSC via Playwright + Chrome logado (CDP 9222).

A API do GSC NAO expoe "Solicitar indexacao" (so dashboard manual). Este script
automatiza o fluxo do dashboard num Chrome ja logado no Google.

PRE-REQUISITOS:
  1. pip3 install playwright --break-system-packages   (so o client, conecta no Chrome existente)
  2. Chrome debug logado no Google com acesso a property:
     "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \\
       --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-debug-profile" \\
       --no-first-run --no-default-browser-check \\
       "https://search.google.com/search-console?resource_id=sc-domain:SEU-DOMINIO"
     (logar manual no Google na 1a vez; sessao persiste no profile)

USO:
  python3 request_indexing.py "sc-domain:digitale.com.br" url1 url2 ...
  (ou edite URLS abaixo e rode sem args)

GOTCHAS (aprendidos 2026-05-22):
  - NAO existe deep-link /search-console/inspect?id=... -> da 404. Usar a barra
    de inspecao do dashboard: input[aria-label*="nspecion"] -> fill -> Enter.
  - O botao "SOLICITAR INDEXACAO" e um <span> com pointer-events:none; clicar com
    force=True (o overlay div pai tem o jsaction).
  - Cota diaria do Google ~10-12 URLs/property. Ao ver "A cota foi excedida", parar.
  - Fechar o dialog (Escape) antes do proximo, senao trans-layer intercepta cliques.
"""
import sys, time
from playwright.sync_api import sync_playwright

RESOURCE = sys.argv[1] if len(sys.argv) > 1 else "sc-domain:digitale.com.br"
URLS = sys.argv[2:] or [
    # edite aqui se rodar sem args
]
DASH = "https://search.google.com/search-console?resource_id=" + RESOURCE.replace(":", "%3A")
DONE = ["Indexação solicitada", "fila de indexação", "solicitação de indexação",
        "Foi feita uma solicitação", "Indexing requested", "adicionado a uma fila"]
QUOTA = ["cota foi excedida", "excedeu sua cota", "cota de solicitações",
         "ultrapassou", "exceeded your quota", "quota exceeded"]

def find_input(pg):
    loc = pg.locator('input[aria-label*="nspecion"]')
    return loc.first if loc.count() > 0 else None

def main():
    if not URLS:
        print("Nenhuma URL. Uso: request_indexing.py RESOURCE url1 url2 ..."); return
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://localhost:9222")
        pg = b.contexts[0].new_page()
        pg.goto(DASH, wait_until="domcontentloaded", timeout=60000); time.sleep(6)
        ok = quota = 0
        for i, u in enumerate(URLS, 1):
            print(f"\n[{i}/{len(URLS)}] {u}", flush=True)
            inp = find_input(pg)
            if not inp:
                pg.goto(DASH, wait_until="domcontentloaded", timeout=60000); time.sleep(6); inp = find_input(pg)
            inp.click(); inp.fill(""); inp.fill(u); pg.keyboard.press("Enter")
            btn = None; dl = time.time() + 80
            while time.time() < dl:
                loc = pg.get_by_text("SOLICITAR INDEXAÇÃO", exact=False)
                try:
                    if loc.count() > 0 and loc.first.is_visible(): btn = loc.first; break
                except Exception: pass
                time.sleep(2)
            if not btn:
                body = pg.inner_text("body")
                print("  ! sem botão", "(já indexada)" if "está indexada" in body else "(inspeção lenta?)", flush=True)
                continue
            btn.click(force=True)
            print("  → clicado, testando...", flush=True)
            res = None; dl = time.time() + 150
            while time.time() < dl:
                body = pg.inner_text("body")
                if any(q in body for q in QUOTA): res = "COTA EXCEDIDA"; break
                if any(d in body for d in DONE): res = "OK"; break
                time.sleep(4)
            print("  =>", res or "timeout", flush=True)
            try: pg.keyboard.press("Escape")
            except Exception: pass
            if res == "OK": ok += 1
            if res == "COTA EXCEDIDA":
                quota = 1; print("\n### COTA DIÁRIA ESGOTADA — parando ###", flush=True); break
            time.sleep(4)
        print(f"\nFIM. solicitadas={ok}, cota_estourou={'sim' if quota else 'não'}", flush=True)

if __name__ == "__main__":
    main()
