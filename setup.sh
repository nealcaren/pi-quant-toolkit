#!/usr/bin/env bash
# One-time setup for the pi-quant-toolkit.
# Prereqs you must install first: Node.js 20+, uv, and (for lit-search) Zotero.
set -euo pipefail

# Where this toolkit lives once hosted — edit before sharing with students.
PKG="git:github.com/nealcaren/pi-quant-toolkit@main"

# --- Node version guard: Pi requires Node >= 22.19.0 ---------------------
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
if [ "$NODE_MAJOR" -lt 22 ]; then
  echo "ERROR: Pi needs Node.js 22.19.0 or newer. You have $(node --version 2>/dev/null || echo 'no node')."
  echo "       Install Node 22 (see README Step 0), then re-run this script."
  echo "       With nvm:  nvm install 22 && nvm alias default 22   (then open a new terminal)"
  exit 1
fi
# ------------------------------------------------------------------------

echo "==> Installing Pi (the coding agent)"
npm install -g @earendil-works/pi-coding-agent@latest

echo "==> Installing the quant-social-science toolkit (skills + bundled extensions)"
# This package bundles its extensions (pi-web-access, ask-user-question,
# plannotator), so this single install brings them along.
pi install "$PKG"

# --- Fallback -------------------------------------------------------------
# If an extension does not load after the install above (check with /extensions
# inside pi), install them explicitly:
#   pi install npm:pi-web-access
#   pi install npm:@juicesharp/rpiv-ask-user-question
#   pi install npm:@plannotator/pi-extension
# --------------------------------------------------------------------------

cat <<'NEXT'

Done. Two things left, by hand:

  1. Connect OpenRouter (this is what you pay per token):
        pi        # then run:  /login openrouter
     or:  export OPENROUTER_API_KEY=sk-or-...

  2. Start Pi on the cheap default model:
        pi --provider openrouter --model deepseek/deepseek-v4-flash-0731
     Switch to the smarter model for hard analysis:
        /model deepseek/deepseek-v4-pro

NEXT
