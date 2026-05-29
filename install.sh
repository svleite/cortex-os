#!/usr/bin/env bash
# Córtex OS — instalador e atualizador (idempotente)
# Instala:  curl -fsSL https://raw.githubusercontent.com/svleite/cortex-os/main/install.sh | bash
# Atualiza: rode de novo (faz git pull) ou: cd ~/.cortex-os && git pull && ./install.sh
set -euo pipefail

REPO_URL="https://github.com/svleite/cortex-os"
CORTEX_HOME="${CORTEX_HOME:-$HOME/.cortex-os}"
SKILLS_DIR="$HOME/.claude/skills"
COMMANDS_DIR="$HOME/.claude/commands"

echo "Córtex OS — instalando/atualizando..."

# 1. clonar ou atualizar o repo canônico
if [ -d "$CORTEX_HOME/.git" ]; then
  echo "→ atualizando $CORTEX_HOME"
  git -C "$CORTEX_HOME" pull --ff-only
else
  echo "→ clonando em $CORTEX_HOME"
  git clone "$REPO_URL" "$CORTEX_HOME"
fi

mkdir -p "$SKILLS_DIR" "$COMMANDS_DIR"

# 2. symlink das skills (atualiza no lugar; -n evita aninhar em re-runs)
echo "→ linkando skills em $SKILLS_DIR"
for d in "$CORTEX_HOME"/skills/*/; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  ln -sfn "${d%/}" "$SKILLS_DIR/$name"
  echo "   skill: $name"
done

# 3. symlink dos comandos do OS
echo "→ linkando comandos em $COMMANDS_DIR"
for f in "$CORTEX_HOME"/commands/*.md; do
  [ -f "$f" ] || continue
  ln -sfn "$f" "$COMMANDS_DIR/$(basename "$f")"
  echo "   comando: /$(basename "$f" .md)"
done

echo ""
echo "Córtex OS pronto. Skills e comandos linkados (symlink) em ~/.claude/."
echo "Como é symlink, todo 'git pull' aqui atualiza tua ferramenta na hora."
echo "Próximo passo: abre o Claude Code e roda /setup."
