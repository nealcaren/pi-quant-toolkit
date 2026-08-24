# One-time setup for the pi-quant-toolkit (Windows / PowerShell).
# Prereqs you must install first: Node.js 20+, uv, and (for lit-search) Zotero.
# Run in PowerShell:  ./setup.ps1
# If blocked by execution policy, run once:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$ErrorActionPreference = "Stop"

# Where this toolkit lives once hosted — edit before sharing with students.
$PKG = "git:github.com/nealcaren/pi-quant-toolkit@main"

# --- Node version guard: Pi requires Node >= 22.19.0 ---------------------
try { $nodeMajor = [int](node -p 'process.versions.node.split(".")[0]') } catch { $nodeMajor = 0 }
if ($nodeMajor -lt 22) {
  Write-Host "ERROR: Pi needs Node.js 22.19.0 or newer. You have $(try { node --version } catch { 'no node' })."
  Write-Host "       Install Node 22 (see README Step 0), then re-run this script."
  Write-Host "       winget install OpenJS.NodeJS.LTS   (then open a new terminal)"
  exit 1
}
# ------------------------------------------------------------------------

Write-Host "==> Installing Pi (the coding agent)"
npm install -g '@earendil-works/pi-coding-agent@latest'

Write-Host "==> Installing the quant-social-science toolkit (skills + bundled extensions)"
# This package bundles its extensions (pi-web-access, ask-user-question,
# plannotator), so this single install brings them along.
pi install $PKG

# --- Fallback -------------------------------------------------------------
# If an extension does not load after the install above (check with /extensions
# inside pi), install them explicitly:
#   pi install npm:pi-web-access
#   pi install npm:@juicesharp/rpiv-ask-user-question
#   pi install npm:@plannotator/pi-extension
# --------------------------------------------------------------------------

Write-Host @"

Done. Two things left, by hand:

  1. Connect OpenRouter (this is what you pay per token):
        pi        # then run:  /login openrouter
     or:  `$env:OPENROUTER_API_KEY = "sk-or-..."

  2. Start Pi on the cheap default model:
        pi --provider openrouter --model deepseek/deepseek-v4-flash-0731
     Switch to the smarter model for hard analysis:
        /model deepseek/deepseek-v4-pro

"@
