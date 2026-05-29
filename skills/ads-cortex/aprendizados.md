# Aprendizados — Ads Córtex

Regras gerais aprendidas durante o uso. O Claude DEVE ler este arquivo no início de qualquer comando.
Regras específicas de plataforma ficam no `aprendizados.md` de cada skill de execução.

---

## Digitale — diagnóstico 2026-05-18

**Contas-chave:**
- Meta marca-própria: `act_2343187982604098` (BRL) + `act_65687989` (USD legacy). Zeradas. Meta BM `1032747920086087` roda só clientes externos.
- Google Ads Digitale: customer `3684009049` (MCC `9854022483`).
- GA4 Digitale property: `387772067`.

**Mix de conversão (30d):**
- 42% Google CPC · 29% Direct (brand) · 13% ChatGPT (AEO) · 13% Google organic · 3% outros
- ChatGPT já entrega ~12% das conv sem investimento dedicado → AEO funciona, vale escalar conteúdo "como/quanto/vale"

**Quality gates Digitale:**
- Search "DGT - LinkedIn p/ Empresas" = motor real (76% das conv pagas). CTR 9,6% ótimo. Search Impression Share 18% = principal alavanca, dobrar budget pra IS ≥40%
- Display GA4 atribui 3-5× mais conv que Google Ads (modelo data-driven vs last-click). Antes de matar Display, conferir se está assistindo Search
- Único canal pago = Google CPC. Diversificação zero. Vulnerabilidade estratégica
- Bounce direct 74% = normal pra brand search/digitação direta, não é alarme

## Cold-start Smart Bidding (Plano RBL 2026-05-20)

**Regra:** Maximizar Conversões (e tCPA/Maximizar valor) precisa de histórico de conversão pra decidir entrar em leilão. Conta nova com 0 conversão registrada + budget minúsculo → o algoritmo se estrangula sozinho (entra em pouquíssimos leilões, gera ~1 imp/dia, 0 clique). Não confundir com "volume de busca baixo": parte da inércia é a estratégia de lance rodando sem dado.

**Diagnóstico:** ENABLED + impressões pífias + 0 clique + 0 conversão + estratégia conversion-based = cold-start deadlock (sem clique nunca vem conversão, sem conversão o lance nunca abre).

**Fix cold start:** trocar pra Maximizar Cliques (ou CPC manual) pra comprar o tráfego que existe e acumular clique→conversão. Subir budget pra não ser o gargalo. Migrar pra Maximizar Conversões só após ~15-30 conv/30d. Validar antes que a conversão (lead form etc.) está configurada e disparando.

**Caso real:** Plano RBL Google `8000027193`, Search Maximizar Conversões + R$6/dia + 0 conv → 27 imp / 0 clique em 30d.
