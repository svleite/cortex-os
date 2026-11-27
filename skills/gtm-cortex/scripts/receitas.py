#!/usr/bin/env python3
"""Receitas prontas de GTM: monta tags, gatilhos e variáveis padrão num workspace.

Sem --confirmar só mostra o PLANO (nada é escrito). Com --confirmar cria o que falta.
Idempotente: item com o mesmo nome no workspace é mantido como está ("ja_existe").
Escrever no workspace NÃO muda o site: o site só muda quando a versão é publicada
(publicar.py). Fluxo: plano -> --confirmar -> Visualizar no GTM (humano) -> publicar.py.

Uso:
  receitas.py base           --container GTM-XXXX --ga4 G-XXXXXXX
  receitas.py google-ads     --container GTM-XXXX --ads AW-123456789
  receitas.py lead-whatsapp  --container GTM-XXXX [--ga4 G-X] [--ads-conversao AW-123/rotulo] [--sem-joinchat] [--sem-links]
  receitas.py lead-telefone  --container GTM-XXXX [--ga4 G-X] [--ads-conversao AW-123/rotulo]
  receitas.py meta-pixel     --container GTM-XXXX --pixel 1234567890 [--lead]
  receitas.py listar         --container GTM-XXXX            (estado atual do workspace)
Opções comuns: --workspace "Nome" (padrão: Default Workspace) · --moeda BRL · --confirmar

Pegadinhas da API embutidas aqui (aprendidas em setup real):
  - conversionId do Google Ads vai SÓ com dígitos (com "AW-" a tag salva mas não dispara)
  - measurementIdOverride do evento GA4 não aceita variável: vai o G- literal
  - nome de tag/gatilho não aceita ":" (usar " - ")
  - Joinchat (WordPress) avisa o GTM com o evento personalizado "JoinChat" e abre o
    WhatsApp por window.open, sem link clicável: por isso dois gatilhos (evento + clique em link)
  - Joinchat + tag do Google instalada direto no código do site = generate_lead duplicado.
    Regra: toda tag do Google dentro do GTM.
"""
import argparse
import re

from gtm_lib import (ALL_PAGES, INITIALIZATION, GTMError, call, listar, main_seguro, p,
                     resolve_container, saida, workspace)

RE_GA4 = re.compile(r"^G-[A-Z0-9]{4,}$")
RE_AW = re.compile(r"^AW-(\d{6,})$")
RE_AW_CONV = re.compile(r"^AW-(\d{6,})/([A-Za-z0-9_-]+)$")
RE_PIXEL = re.compile(r"^\d{10,20}$")

WHATSAPP_URL_RE = r"wa\.me/|api\.whatsapp\.com|web\.whatsapp\.com|^whatsapp:"
TELEFONE_URL_RE = r"^tel:"

# ---------- blocos de construção (corpos no formato da API v2) ----------

def tag(nome, tipo, params, gatilhos, notas):
    return {"kind": "tag", "name": nome,
            "body": {"name": nome, "type": tipo, "parameter": params, "notes": notas,
                     "firingTriggerId": gatilhos}}


def gatilho_evento(nome, evento, notas):
    return {"kind": "trigger", "name": nome, "body": {
        "name": nome, "type": "customEvent", "notes": notas,
        "customEventFilter": [{"type": "equals", "parameter": [
            p("arg0", "{{_event}}"), p("arg1", evento)]}]}}


def gatilho_link(nome, regex, notas):
    return {"kind": "trigger", "name": nome, "body": {
        "name": nome, "type": "linkClick", "notes": notas,
        "waitForTags": {"type": "boolean", "value": "false"},
        "checkValidation": {"type": "boolean", "value": "false"},
        "filter": [{"type": "matchRegex", "parameter": [
            p("arg0", "{{Click URL}}"), p("arg1", regex), p("ignore_case", "true", "boolean")]}]}}


def builtins(*tipos):
    return {"kind": "builtin", "name": "variáveis nativas: " + ", ".join(tipos), "types": list(tipos)}


def evento_ga4(nome, ga4, evento, params, gatilhos, notas):
    tabela = {"type": "list", "key": "eventSettingsTable", "list": [
        {"type": "map", "map": [p("parameter", k), p("parameterValue", v)]} for k, v in params]}
    return tag(nome, "gaawe", [p("eventName", evento), p("measurementIdOverride", ga4), tabela],
               gatilhos, notas)


def conversao_ads(nome, aw_id, rotulo, moeda, gatilhos, notas):
    return tag(nome, "awct", [p("conversionId", aw_id), p("conversionLabel", rotulo),
                              p("currencyCode", moeda)], gatilhos, notas)


def vinculador():
    return tag("Google - Vinculador de conversões", "gclidw", [], [ALL_PAGES],
               "Guarda o clique do anúncio (gclid) em cookie próprio pra conversão ser atribuída.")


# ---------- receitas ----------

def r_base(a):
    if not a.ga4 or not RE_GA4.match(a.ga4):
        raise GTMError("base exige --ga4 G-XXXXXXX")
    return [
        tag(f"Google - Tag do Google ({a.ga4})", "googtag", [p("tagId", a.ga4)], [INITIALIZATION],
            "Tag do Google do GA4. Dispara na inicialização, antes das demais tags."),
        vinculador(),
    ]


def r_google_ads(a):
    m = RE_AW.match(a.ads or "")
    if not m:
        raise GTMError("google-ads exige --ads AW-123456789 (sem rótulo)")
    digitos = m.group(1)
    return [
        tag(f"Ads - Tag do Google ({a.ads})", "googtag", [p("tagId", a.ads)], [INITIALIZATION],
            "Tag do Google da conta de anúncios (tag global)."),
        tag(f"Ads - Remarketing ({a.ads})", "sp", [p("conversionId", digitos)], [ALL_PAGES],
            "Alimenta os públicos de visitantes do site no Google Ads."),
        vinculador(),
    ]


ROTULO = {"whatsapp": "WhatsApp", "telefone": "Telefone"}


def _lead(a, canal, gatilhos_nomes, passos):
    if not a.ga4 and not a.ads_conversao:
        raise GTMError(f"lead-{canal} precisa de pelo menos um destino: --ga4 e/ou --ads-conversao")
    if a.ga4 and not RE_GA4.match(a.ga4):
        raise GTMError("--ga4 inválido (esperado G-XXXXXXX)")
    refs = ["@" + n for n in gatilhos_nomes]
    if a.ga4:
        passos.append(evento_ga4(f"GA4 - generate_lead - {ROTULO[canal]}", a.ga4, "generate_lead",
                                 [("method", canal), ("link_url", "{{Click URL}}"), ("page_location", "{{Page URL}}")],
                                 refs, f"Lead por {canal}. generate_lead é o evento recomendado do GA4: "
                                       "depois de publicar, marcar como evento principal no GA4."))
    if a.ads_conversao:
        m = RE_AW_CONV.match(a.ads_conversao)
        if not m:
            raise GTMError("--ads-conversao inválido (esperado AW-123456789/rotulo)")
        passos.append(conversao_ads(f"Ads - Conversão - {ROTULO[canal]}", m.group(1), m.group(2),
                                    a.moeda, refs, f"Conversão do Google Ads no clique de {canal}."))
    return passos


def r_lead_whatsapp(a):
    if a.sem_joinchat and a.sem_links:
        raise GTMError("--sem-joinchat e --sem-links juntos deixam a receita sem gatilho")
    passos, nomes = [builtins("clickUrl", "clickText", "pageUrl")], []
    if not a.sem_joinchat:
        passos.append(gatilho_evento("WhatsApp - Botão Joinchat", "JoinChat",
                                     "Plugin Joinchat (WordPress) faz dataLayer.push({event:'JoinChat'}) no clique."))
        nomes.append("WhatsApp - Botão Joinchat")
    if not a.sem_links:
        passos.append(gatilho_link("WhatsApp - Clique em link", WHATSAPP_URL_RE,
                                   "Links wa.me / api.whatsapp.com / whatsapp: soltos na página."))
        nomes.append("WhatsApp - Clique em link")
    return _lead(a, "whatsapp", nomes, passos)


def r_lead_telefone(a):
    passos = [builtins("clickUrl", "clickText", "pageUrl"),
              gatilho_link("Telefone - Clique em link", TELEFONE_URL_RE, "Links tel: (ligação pelo celular).")]
    return _lead(a, "telefone", ["Telefone - Clique em link"], passos)


PIXEL_BASE = """<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '{PIXEL}');
fbq('track', 'PageView');
</script>"""


def r_meta_pixel(a):
    if not RE_PIXEL.match(a.pixel or ""):
        raise GTMError("meta-pixel exige --pixel com o ID numérico do pixel")
    passos = [tag("Meta - Pixel base (PageView)", "html",
                  [p("html", PIXEL_BASE.replace("{PIXEL}", a.pixel)), p("supportDocumentWrite", "false", "boolean")],
                  [ALL_PAGES], f"Código base do Meta Pixel {a.pixel}.")]
    if a.lead:
        passos.append(tag("Meta - Lead - WhatsApp", "html",
                          [p("html", "<script>if(window.fbq)fbq('track','Lead');</script>"),
                           p("supportDocumentWrite", "false", "boolean")],
                          ["@WhatsApp - Botão Joinchat", "@WhatsApp - Clique em link"],
                          "Lead no Meta no clique de WhatsApp. Exige os gatilhos da receita lead-whatsapp."))
    return passos


RECEITAS = {"base": r_base, "google-ads": r_google_ads, "lead-whatsapp": r_lead_whatsapp,
            "lead-telefone": r_lead_telefone, "meta-pixel": r_meta_pixel}

# ---------- plano e execução ----------

def _params(t):
    return {x.get("key"): x.get("value") for x in t.get("parameter", []) if x.get("type") in ("template", "boolean")}


def chave(t):
    """Identidade FUNCIONAL da tag, independente do nome dado por quem montou o container.
    Evita duplicar o que já existe com outro nome (ex.: um 2º vinculador de conversões)."""
    tipo, pr = t.get("type"), _params(t)
    if tipo == "gclidw":
        return ("gclidw",)
    if tipo == "googtag":
        return ("googtag", (pr.get("tagId") or "").upper())
    if tipo == "sp":
        return ("sp", pr.get("conversionId"))
    if tipo == "awct":
        return ("awct", pr.get("conversionId"), pr.get("conversionLabel"))
    if tipo == "html":
        m = re.search(r"fbq\(\s*['\"]init['\"]\s*,\s*['\"](\d+)['\"]", pr.get("html") or "")
        if m:
            return ("meta-pixel", m.group(1))
    return None


def planejar(passos, ws_path):
    existentes = listar(ws_path, "tags")
    tags = {t["name"]: t for t in existentes}
    por_chave = {}
    for t in existentes:
        k = chave(t)
        if k and k not in por_chave:
            por_chave[k] = t
    trigs = {t["name"]: t for t in listar(ws_path, "triggers")}
    nativas = {b["type"] for b in listar(ws_path, "built_in_variables")}
    plano = []
    for s in passos:
        if s["kind"] == "builtin":
            faltam = [t for t in s["types"] if t not in nativas]
            plano.append(dict(s, acao="ativar" if faltam else "ja_existe", types=faltam or s["types"]))
        elif s["kind"] == "trigger":
            existe = trigs.get(s["name"])
            plano.append(dict(s, acao="ja_existe" if existe else "criar", id=(existe or {}).get("triggerId")))
        else:
            existe = tags.get(s["name"])
            k = chave(s["body"])
            equivalente = None if existe else por_chave.get(k) if k else None
            if equivalente:
                plano.append(dict(s, acao="ja_existe", id=equivalente["tagId"],
                                  obs=f"equivalente já existe como '{equivalente['name']}'"))
            else:
                plano.append(dict(s, acao="ja_existe" if existe else "criar", id=(existe or {}).get("tagId")))
    # gatilho referenciado precisa existir no workspace ou ser criado neste plano
    disponiveis = set(trigs) | {s["name"] for s in plano if s["kind"] == "trigger"}
    for s in plano:
        if s["kind"] == "tag" and s["acao"] == "criar":
            faltando = [g[1:] for g in s["body"]["firingTriggerId"] if g.startswith("@") and g[1:] not in disponiveis]
            if faltando:
                raise GTMError(f"Tag '{s['name']}' depende de gatilho inexistente: {faltando}. Rode a receita que cria esses gatilhos antes.")
    return plano


def executar(plano, ws_path):
    ids = {t["name"]: t["triggerId"] for t in listar(ws_path, "triggers")}
    feitos = []
    for s in plano:
        if s["acao"] == "ja_existe":
            continue
        if s["kind"] == "builtin":
            call("POST", f"/{ws_path}/built_in_variables", query={"type": s["types"]})
            feitos.append({"ativado": s["types"]})
        elif s["kind"] == "trigger":
            r = call("POST", f"/{ws_path}/triggers", s["body"])
            ids[r["name"]] = r["triggerId"]
            feitos.append({"gatilho": r["name"], "id": r["triggerId"]})
        else:
            body = dict(s["body"])
            body["firingTriggerId"] = [ids[g[1:]] if g.startswith("@") else g for g in body["firingTriggerId"]]
            r = call("POST", f"/{ws_path}/tags", body)
            feitos.append({"tag": r["name"], "id": r["tagId"]})
    return feitos


def resumo(plano):
    return [dict({"acao": s["acao"], "tipo": s["kind"], "nome": s["name"]}, **({"obs": s["obs"]} if s.get("obs") else {}))
            for s in plano]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("receita", choices=sorted(RECEITAS) + ["listar"])
    ap.add_argument("--container", required=True, help="ID público, ex.: GTM-XXXXXXX")
    ap.add_argument("--workspace")
    ap.add_argument("--ga4")
    ap.add_argument("--ads")
    ap.add_argument("--ads-conversao")
    ap.add_argument("--pixel")
    ap.add_argument("--lead", action="store_true")
    ap.add_argument("--sem-joinchat", action="store_true")
    ap.add_argument("--sem-links", action="store_true")
    ap.add_argument("--moeda", default="BRL")
    ap.add_argument("--confirmar", action="store_true")
    a = ap.parse_args()

    ctr = resolve_container(a.container)
    ws = workspace(ctr, a.workspace)
    cab = {"container": ctr["public_id"], "nome": ctr["name"], "workspace": ws["name"]}

    if a.receita == "listar":
        saida(dict(cab,
                   tags=[f"{t['name']}  [{t['type']}]" for t in listar(ws["path"], "tags")],
                   gatilhos=[f"{t['name']}  [{t['type']}]" for t in listar(ws["path"], "triggers")],
                   nativas=[b["type"] for b in listar(ws["path"], "built_in_variables")]))
        return

    plano = planejar(RECEITAS[a.receita](a), ws["path"])
    if not a.confirmar:
        saida(dict(cab, receita=a.receita, modo="PRÉVIA (nada foi escrito)", plano=resumo(plano),
                   proximo="Mostrar o plano ao usuário. Com ok explícito, repetir com --confirmar."))
        return
    feitos = executar(plano, ws["path"])
    saida(dict(cab, receita=a.receita, modo="APLICADO no workspace (o site ainda não mudou)", feitos=feitos,
               proximo="Testar no modo Visualizar do GTM; depois publicar.py versao/publicar."))


if __name__ == "__main__":
    main_seguro(main)
