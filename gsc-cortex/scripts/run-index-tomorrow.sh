#!/bin/zsh
# One-shot agendado (launchd) para Request Indexing GSC das URLs pendentes.
# Roda só em/após 2026-05-23, garante Chrome debug logado, dispara o script,
# e se auto-remove (one-shot). Log em ~/.claude/.../gsc-index-DATA.log
set -u

LOGDIR="$HOME/.claude/projects/-Users-samuelleite-Documents-Dev---Maker-Estudos"
LOG="$LOGDIR/gsc-index-$(date +%F).log"
PY="/Users/samuelleite/Documents/Dev & Maker/Estudos/.claude/skills/relatorio-linkedin/scripts/.venv/bin/python3"
SCRIPT="$HOME/.claude/skills/gsc-cortex/scripts/request_indexing.py"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
RESOURCE="sc-domain:digitale.com.br"
URLS=(
  "https://digitale.com.br/series-em-video/"
  "https://digitale.com.br/series-em-video/vivo/"
  "https://digitale.com.br/series-em-video/honda/"
  "https://digitale.com.br/series-em-video/astrazeneca/"
  "https://digitale.com.br/series-em-video/microsoft/"
  "https://digitale.com.br/series-em-video/bosch/"
  "https://digitale.com.br/series-em-video/arteris/"
  "https://digitale.com.br/livros/conecte-primeiro-capitulo/"
)

echo "=== run $(date) ===" >> "$LOG"

# guarda: não rodar antes de 2026-05-23
if [[ $(date +%Y%m%d) -lt 20260523 ]]; then
  echo "antes de 2026-05-23, pulando" >> "$LOG"; exit 0
fi

# garante Chrome debug 9222 logado
if ! curl -s http://localhost:9222/json/version >/dev/null 2>&1; then
  echo "subindo Chrome debug..." >> "$LOG"
  "$CHROME" --remote-debugging-port=9222 \
    --user-data-dir="$HOME/.chrome-debug-profile" \
    --no-first-run --no-default-browser-check \
    "https://search.google.com/search-console?resource_id=$RESOURCE" >/dev/null 2>&1 &
  sleep 12
fi

"$PY" "$SCRIPT" "$RESOURCE" "${URLS[@]}" >> "$LOG" 2>&1
echo "=== fim $(date) ===" >> "$LOG"

# one-shot: remove o agendamento
launchctl bootout "gui/$(id -u)/com.digitale.gsc-index" 2>/dev/null
rm -f "$HOME/Library/LaunchAgents/com.digitale.gsc-index.plist"
echo "agendamento removido (one-shot)" >> "$LOG"
