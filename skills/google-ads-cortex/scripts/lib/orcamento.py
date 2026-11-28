"""Trava de orçamento: prévia em reais, confirmação explícita e limite de aumento.

Toda escrita que cria ou muda orçamento (diário, vitalício ou teto de gasto) passa por
`checar()` antes de chamar a API:

- mostra o antes e o depois em moeda, nunca em centavos ou micros;
- sem `--confirmar`, só mostra a prévia e sai sem alterar nada;
- recusa aumento acima de LIMITE_AUMENTO (1,5 = +50%) sobre o valor atual, e valor
  diário acima de `teto_diario_reais` da conta no contas.yaml, salvo `--acima-do-limite`;
- registra cada mudança aplicada em logs/orcamento.jsonl, na pasta da skill.

Mesmo arquivo em meta-ads-cortex e google-ads-cortex: alterar os dois juntos.
"""
import json
import os
import sys
import time

LIMITE_AUMENTO = 1.5
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROTULO = {
    "daily_budget": "orçamento diário",
    "lifetime_budget": "orçamento vitalício",
    "spend_cap": "teto de gasto",
}


def add_args(parser):
    parser.add_argument("--confirmar", action="store_true",
                        help="aplica a mudança de orçamento (sem isso, só mostra a prévia)")
    parser.add_argument("--acima-do-limite", dest="acima_do_limite", action="store_true",
                        help=f"libera aumento acima de {int((LIMITE_AUMENTO - 1) * 100)}%% "
                             "ou acima do teto diário da conta")


def moeda_fmt(centavos, moeda="BRL"):
    if centavos is None:
        return "nenhum"
    valor = int(centavos) / 100
    simbolo = {"BRL": "R$", "USD": "US$", "EUR": "€"}.get(moeda, moeda)
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{simbolo} {texto}"


def teto_diario(conta_id):
    """teto_diario_reais da conta no contas.yaml da skill (None se não houver)."""
    caminho = os.path.join(SKILL_DIR, "contas.yaml")
    if not conta_id or not os.path.exists(caminho):
        return None
    try:
        import yaml
        with open(caminho, encoding="utf-8") as f:
            dados = yaml.safe_load(f) or {}
    except Exception:
        return None
    alvo = str(conta_id).replace("act_", "").replace("-", "")

    def procura(no):
        if isinstance(no, dict):
            ids = [str(no.get(k, "")).replace("act_", "").replace("-", "")
                   for k in ("conta_anuncio", "customer_id", "account_id")]
            if alvo in ids and no.get("teto_diario_reais") is not None:
                return int(round(float(no["teto_diario_reais"]) * 100))
            for v in no.values():
                r = procura(v)
                if r is not None:
                    return r
        elif isinstance(no, list):
            for v in no:
                r = procura(v)
                if r is not None:
                    return r
        return None

    return procura(dados)


def checar(args, objeto, campos, conta_id=None, moeda="BRL"):
    """campos = {"daily_budget": (atual_centavos_ou_None, novo_centavos), ...}.

    Volta só se puder aplicar. Prévia sai com código 0; bloqueio sai com código 2.
    """
    campos = {k: (None if a in (None, "", 0, "0") else int(a), int(n))
              for k, (a, n) in campos.items() if n not in (None, "")}
    if not campos:
        return
    teto = teto_diario(conta_id)
    print(f"\nOrçamento: {objeto}", file=sys.stderr)
    bloqueios, invalidos = [], []
    for campo, (atual, novo) in campos.items():
        nome = ROTULO.get(campo, campo)
        if novo <= 0:
            invalidos.append(f"{nome}: valor {novo} inválido")
            continue
        fator = f" ({novo / atual:.1f}x)" if atual else ""
        print(f"  {nome}: {moeda_fmt(atual, moeda)} → {moeda_fmt(novo, moeda)}{fator}", file=sys.stderr)
        if atual and novo > atual * LIMITE_AUMENTO:
            bloqueios.append(f"{nome} sobe {novo / atual:.1f}x (limite: {LIMITE_AUMENTO:.1f}x)")
        if campo == "daily_budget" and teto and novo > teto:
            bloqueios.append(f"{nome} acima do teto diário da conta ({moeda_fmt(teto, moeda)})")
    if invalidos:
        print("\nBLOQUEADO, nada foi alterado: " + "; ".join(invalidos), file=sys.stderr)
        sys.exit(2)
    if bloqueios and not getattr(args, "acima_do_limite", False):
        print("\nBLOQUEADO, nada foi alterado:", file=sys.stderr)
        for b in bloqueios:
            print(f"  - {b}", file=sys.stderr)
        print("Confira o valor (em centavos: 5000 = R$ 50,00). Se for intencional e o usuário "
              "aprovou, repita com --acima-do-limite --confirmar.", file=sys.stderr)
        sys.exit(2)
    if not getattr(args, "confirmar", False):
        print("\nPRÉVIA: nada foi alterado. Confirme o valor com o usuário e repita com --confirmar.",
              file=sys.stderr)
        sys.exit(0)
    registrar(objeto, campos, conta_id, moeda, bool(bloqueios))


def registrar(objeto, campos, conta_id, moeda, liberado_acima):
    try:
        pasta = os.path.join(SKILL_DIR, "logs")
        os.makedirs(pasta, exist_ok=True)
        with open(os.path.join(pasta, "orcamento.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "objeto": objeto, "conta": conta_id, "moeda": moeda,
                "campos": {k: {"antes": a, "depois": n} for k, (a, n) in campos.items()},
                "acima_do_limite": liberado_acima,
            }, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[aviso] não registrei a mudança de orçamento: {e}", file=sys.stderr)
