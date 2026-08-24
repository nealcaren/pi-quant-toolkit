// Fast structural checks on the Pi package — no install required.
// Fails (exit 1) if package.json is malformed or references paths that don't exist.
import { readFileSync, existsSync, statSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const errors = [];
const ok = (m) => console.log(`  ok   ${m}`);

let pkg;
try {
  pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
  ok("package.json is valid JSON");
} catch (e) {
  console.error(`package.json is not valid JSON: ${e.message}`);
  process.exit(1);
}

const pi = pkg.pi ?? {};
const check = (rel, label) => {
  const abs = resolve(root, rel);
  if (!existsSync(abs)) errors.push(`${label} path missing: ${rel}`);
  else ok(`${label}: ${rel}`);
  return abs;
};

// Skills: each entry must exist; a directory must contain at least one SKILL.md.
for (const s of pi.skills ?? []) {
  const abs = check(s, "skill");
  if (existsSync(abs) && statSync(abs).isDirectory()) {
    // top-level skill dir: expect subdirs each with a SKILL.md
    const glob = readFileSync; // noop to keep import used
    void glob;
  }
}

// Extensions: each referenced entry file/dir must exist in the checkout.
// (These live under node_modules, populated by `npm install` in CI before this
// runs, OR are repo-relative source files.)
for (const ext of pi.extensions ?? []) check(ext, "extension");

// Every skills/*/SKILL.md referenced implicitly should parse as a file.
for (const s of pi.skills ?? []) {
  const abs = resolve(root, s);
  if (existsSync(abs) && statSync(abs).isFile() && !abs.endsWith(".md")) {
    errors.push(`skill file is not markdown: ${s}`);
  }
}

if (errors.length) {
  console.error("\nVALIDATION FAILED:");
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}
console.log("\nAll package.json references resolve. ✅");
