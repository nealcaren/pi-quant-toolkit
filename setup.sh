#!/usr/bin/env bash
# One-command setup for the pi-quant-toolkit (macOS / Linux).
# Safe to run straight from the web:
#   curl -fsSL https://raw.githubusercontent.com/nealcaren/pi-quant-toolkit/main/setup.sh | bash
# Requires Node.js 22.19+ installed first (see the README).
set -euo pipefail

PKG="git:github.com/nealcaren/pi-quant-toolkit@main"
CHEAP_MODEL="deepseek/deepseek-v4-flash-0731"

# 1. Check Node.js is new enough (Pi needs 22.19+).
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
if [ "$NODE_MAJOR" -lt 22 ]; then
  echo "ERROR: Pi needs Node.js 22.19 or newer. You have: $(node --version 2>/dev/null || echo 'no Node.js found')."
  echo "       Install Node.js 22 from https://nodejs.org (pick the '22 LTS' button), then run this again."
  exit 1
fi

# 2. Install the Pi agent.
echo "==> Installing Pi (the coding assistant)..."
npm install -g @earendil-works/pi-coding-agent@latest

# 3. Install this toolkit (skills + bundled web-search/ask/plan extensions).
echo "==> Installing the quant toolkit..."
pi install "$PKG"

# 4. Point Pi at the cheap model by default (only if you haven't chosen one).
echo "==> Setting the default model..."
node - "$CHEAP_MODEL" <<'NODE'
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const model = process.argv[2];
const p = path.join(os.homedir(), ".pi", "agent", "settings.json");
let s = {};
try { s = JSON.parse(fs.readFileSync(p, "utf8")); } catch {}
if (s.defaultModel) {
  console.log(`    (kept your existing default: ${s.defaultModel})`);
} else {
  s.defaultProvider = "openrouter";
  s.defaultModel = model;
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(s, null, 2) + "\n");
  console.log(`    default model set to ${model}`);
}
NODE

cat <<'NEXT'

==> All set! One thing left to do by hand:

  Start Pi and connect your OpenRouter account (this is what pays per use):

      pi
      /login openrouter        <- type this once Pi is open

  After that, just run  pi  in any project folder and describe your task.
  Need more power for a hard analysis?  Type:  /model openrouter/deepseek/deepseek-v4-pro

NEXT
