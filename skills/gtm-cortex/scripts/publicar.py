#!/usr/bin/env python3
"""Publicação segura de container GTM: prévia, publicação, reversão e prova no site.

Uso:
  publicar.py status     --container GTM-XXXX [--workspace "Nome"]
  publicar.py publicar   --container GTM-XXXX --nome "v3 - lead WhatsApp" [--notas "..."] [--confirmar]
  publicar.py voltar     --container GTM-XXXX --versao 12 [--confirmar]
  publicar.py verificar  --container GTM-XXXX --site https://exemplo.com.br [--procurar G-X,AW-123,JoinChat]

publicar/voltar sem --confirmar só mostram o que iria ao ar. Só publicar depois de testar
no modo Visualizar do GTM. Publicar consome o workspace (o GTM abre um novo): não guardar o ID dele.
verificar sai com código 1 se o snippet não está no site ou se algum termo procurado não está no gtm.js.
"""
import argparse
import sys
import urllib.request

from gtm_lib import GTMError, call, main_seguro, resolve_container, saida, workspace

UA = {"User-Agent": "Mozilla/5.0 (Macintosh) gtm-cortex/verificar"}


def mudancas(ws):
    st = call("GET", f"/{ws['path']}/status")
    out = []
    for ch in st.get("workspaceChange", []):
        for tipo in ("tag", "trigger", "variable", "folder", "builtInVariable", "client", "template"):
            if tipo in ch:
                item = ch[tipo]
                out.append({"mudanca": ch.get("changeStatus"), "tipo": tipo,
                            "nome": item.get("name") or item.get("type")})
    return out, st.get("mergeConflict", [])


def baixar(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["status", "publicar", "voltar", "verificar"])
    ap.add_argument("--container", required=True)
    ap.add_argument("--workspace")
    ap.add_argument("--nome")
    ap.add_argument("--notas", default="")
    ap.add_argument("--versao")
    ap.add_argument("--site")
    ap.add_argument("--procurar", default="")
    ap.add_argument("--confirmar", action="store_true")
    a = ap.parse_args()

    if a.acao == "verificar":
        if not a.site:
            raise GTMError("verificar exige --site https://...")
        gid = a.container.strip().upper()
        html = baixar(a.site)
        js = baixar(f"https://www.googletagmanager.com/gtm.js?id={gid}")
        termos = [t.strip() for t in a.procurar.split(",") if t.strip()]
        achados = {t: (t in js) for t in termos}
        ok = (gid in html) and all(achados.values())
        saida({"container": gid, "site": a.site, "snippet_no_site": gid in html,
               "no_gtm_js_publicado": achados, "ok": ok,
               "obs": "gtm.js é o container PUBLICADO; o que está só no workspace não aparece aqui."})
        sys.exit(0 if ok else 1)

    ctr = resolve_container(a.container)
    cab = {"container": ctr["public_id"], "nome": ctr["name"]}

    if a.acao == "voltar":
        if not a.versao:
            raise GTMError("voltar exige --versao N (ID da versão a republicar)")
        v = call("GET", f"/{ctr['path']}/versions/{a.versao}")
        if not a.confirmar:
            saida(dict(cab, modo="PRÉVIA", republicaria={"versao": a.versao, "nome": v.get("name"),
                       "tags": len(v.get("tag", [])), "gatilhos": len(v.get("trigger", []))},
                       proximo="Com ok explícito, repetir com --confirmar."))
            return
        call("POST", f"/{ctr['path']}/versions/{a.versao}:publish")
        saida(dict(cab, modo="REPUBLICADO", versao=a.versao, nome=v.get("name")))
        return

    ws = workspace(ctr, a.workspace)
    lista, conflitos = mudancas(ws)
    if a.acao == "status":
        saida(dict(cab, workspace=ws["name"], mudancas=lista, conflitos=len(conflitos)))
        return

    # publicar
    if not a.nome:
        raise GTMError('publicar exige --nome "descrição da versão"')
    if conflitos:
        raise GTMError(f"Workspace com {len(conflitos)} conflito(s) de merge: resolver no GTM antes.")
    if not lista:
        raise GTMError("Workspace sem mudanças: nada a publicar.")
    if not a.confirmar:
        saida(dict(cab, workspace=ws["name"], modo="PRÉVIA (nada publicado)", iria_ao_ar=lista,
                   proximo="Testar no modo Visualizar do GTM. Com ok explícito, repetir com --confirmar."))
        return
    cv = call("POST", f"/{ws['path']}:create_version", {"name": a.nome, "notes": a.notas})
    ver = cv.get("containerVersion") or {}
    vid = ver.get("containerVersionId")
    if not vid:
        raise GTMError(f"Versão não criada: {str(cv)[:300]}")
    call("POST", f"/{ctr['path']}/versions/{vid}:publish")
    saida(dict(cab, modo="PUBLICADO", versao=vid, nome=a.nome,
               proximo=f"publicar.py verificar --container {ctr['public_id']} --site <url> --procurar <ids>"))


if __name__ == "__main__":
    main_seguro(main)
