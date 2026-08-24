# One-command setup for the pi-quant-toolkit (Windows / PowerShell).
# Safe to run straight from the web:
#   irm https://raw.githubusercontent.com/nealcaren/pi-quant-toolkit/main/setup.ps1 | iex
# Requires Node.js 22.19+ installed first (see the README).
$ErrorActionPreference = "Stop"

$PKG = "git:github.com/nealcaren/pi-quant-toolkit@main"
$CheapModel = "deepseek/deepseek-v4-flash-0731"

# 1. Check Node.js is new enough (Pi needs 22.19+).
try { $nodeMajor = [int](node -p 'process.versions.node.split(".")[0]') } catch { $nodeMajor = 0 }
if ($nodeMajor -lt 22) {
  Write-Host "ERROR: Pi needs Node.js 22.19 or newer. You have: $(try { node --version } catch { 'no Node.js found' })."
  Write-Host "       Install Node.js 22 from https://nodejs.org (pick the '22 LTS' button), then run this again."
  exit 1
}

# 2. Install the Pi agent.
Write-Host "==> Installing Pi (the coding assistant)..."
npm install -g '@earendil-works/pi-coding-agent@latest'

# 3. Install this toolkit (skills + bundled web-search/ask/plan extensions).
Write-Host "==> Installing the quant toolkit..."
pi install $PKG

# 4. Point Pi at the cheap model by default (only if you haven't chosen one).
Write-Host "==> Setting the default model..."
$node = @'
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
'@
$node | node - $CheapModel

Write-Host @"

==> All set! One thing left to do by hand:

  Start Pi and connect your OpenRouter account (this is what pays per use):

      pi
      /login openrouter        <- type this once Pi is open

  After that, just run  pi  in any project folder and describe your task.
  Need more power for a hard analysis?  Type:  /model openrouter/deepseek/deepseek-v4-pro

"@
