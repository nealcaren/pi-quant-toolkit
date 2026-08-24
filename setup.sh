#!/usr/bin/env bash
# One-time setup for the pi-quant-toolkit.
# Installs Pi, this package, and the recommended extensions.
# Prereqs you must install first: Node.js 20+, uv, and (for lit-search) Zotero.
set -euo pipefail

# Where this toolkit lives once hosted — edit before sharing with students.
PKG="git:github.com/<your-org>/pi-quant-toolkit@main"

echo "==> Installing Pi (the coding agent)"
npm install -g @earendil-works/pi-coding-agent

echo "==> Installing the quant-social-science toolkit"
pi install "$PKG"

echo "==> Installing recommended extensions"
# Web search + URL/PDF fetch (zero-config: uses Exa, no API key needed)
pi install npm:pi-web-access
# Structured clarifying questions instead of the model guessing
pi install npm:rpiv-ask-user-question

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
