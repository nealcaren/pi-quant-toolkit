# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
reconcile_report.py — catch hallucinated statistics in a write-up.

Every number in a report's prose should trace back to a value the analysis
actually computed. This tool reads a results ledger (JSON the analysis scripts
wrote — see the stat-check skill) and a drafted report (markdown/text), extracts
every numeric token in the prose, and reconciles each against the ledger.

It flags ORPHANS: numbers in the prose that appear nowhere in the computed
results — the signature of a hand-typed / hallucinated statistic. Structural
references (Table 2, Model 3), p-value thresholds (p < .05), and years are
categorized separately so they don't drown the signal.

Matching is value-based and rounding-aware: a prose "0.34" matches a ledger
0.3421, "1,204" matches 1204, "34%" matches 0.34 or 34. The ledger schema is not
enforced — every number anywhere in the JSON counts as "known" — so it works
whatever shape your scripts emit.

Usage (run with uv):
  uv run reconcile_report.py --report memos/analysis-memo.md --ledger output/results.json
  uv run reconcile_report.py --report report.md --ledger results.json --warn-only
  uv run reconcile_report.py --report report.md --ledger results.json --tol 0.01

Exit status: 0 if no orphans; 1 if orphans found (so it gates a workflow);
2 on usage/IO error. --warn-only forces exit 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# A numeric token: optional sign, thousands-grouped or plain digits, optional
# decimal, optional scientific exponent, optional trailing percent. The
# lookbehind/ahead keep us from slicing numbers out of identifiers or dates like
# 2020-01 (the '-' there is not a sign we want).
NUM_RE = re.compile(
    r"(?<![\w.])"
    r"([-+]?(?:\d{1,3}(?:,\d{3})+|\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)(%?)"
    r"(?![\w])"
)

STRUCTURAL_WORDS = (
    "table", "figure", "fig", "model", "column", "col", "section", "panel",
    "appendix", "equation", "eq", "step", "phase", "chapter", "note",
    "footnote", "row", "spec", "specification", "hypothesis", "h",
)
# p-value threshold statements: "p < .05", "p<0.01", "p = .034"
P_THRESHOLD_RE = re.compile(r"\bp\s*[<>=≤≥]\s*0?\.\d+", re.IGNORECASE)
# Words after a percentage that mark it as a convention, not a data value:
# "5% level", "95% confidence interval", "1% significance".
CONVENTION_FOLLOW = ("level", "confidence", "interval", "significance",
                     "ci", "significant", "cl")


def harvest_numbers(obj, path="", out=None):
    """Recursively collect every numeric leaf in the ledger JSON as
    (value: float, path: str). Strings that are cleanly numeric count too."""
    if out is None:
        out = []
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        out.append((float(obj), path or "(root)"))
    elif isinstance(obj, str):
        s = obj.strip().replace(",", "").rstrip("%")
        try:
            out.append((float(s), path or "(root)"))
        except ValueError:
            pass
    elif isinstance(obj, dict):
        for k, v in obj.items():
            harvest_numbers(v, f"{path}.{k}" if path else str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            harvest_numbers(v, f"{path}[{i}]", out)
    return out


def decimals_of(token: str) -> int:
    """How many decimal places the reported token carries (0 if integer)."""
    t = token.replace(",", "")
    if "e" in t.lower():
        # normalize scientific to a plain decimal count
        t = f"{float(t):.15f}".rstrip("0")
    return len(t.split(".")[1]) if "." in t else 0


def matches(cand: float, known: list[tuple[float, str]], decimals: int, tol: float):
    """Return the list of ledger paths whose value matches cand, comparing at the
    precision the prose used (with an absolute tolerance floor)."""
    hits = []
    for val, path in known:
        # Rounding-aware: round the ledger value to the prose's precision.
        rv = round(val, decimals)
        if abs(rv - cand) <= max(tol, 0.5 * 10 ** (-decimals) + 1e-9):
            hits.append(path)
        elif decimals == 0 and abs(val - cand) <= tol:
            hits.append(path)
    return hits


def preceding_word(line: str, start: int) -> str:
    before = line[:start].rstrip()
    m = re.search(r"([A-Za-z.]+)\s*[:#]?\s*$", before)
    return m.group(1).rstrip(".").lower() if m else ""


def following_word(line: str, end: int) -> str:
    after = line[end:].lstrip()
    m = re.match(r"([A-Za-z.]+)", after)
    return m.group(1).rstrip(".").lower() if m else ""


def classify_and_check(report_text: str, known, tol: float):
    results = []  # dicts: value, token, line_no, line, category, ledger_paths
    for lineno, line in enumerate(report_text.splitlines(), 1):
        # Mark spans that are p-value thresholds so their numbers are excused.
        p_spans = [m.span() for m in P_THRESHOLD_RE.finditer(line)]
        for m in NUM_RE.finditer(line):
            raw, pct = m.group(1), m.group(2)
            start = m.start()
            token = raw + pct
            in_p = any(s <= start < e for s, e in p_spans)
            norm = raw.replace(",", "")
            try:
                base = float(norm)
            except ValueError:
                continue
            dec = decimals_of(raw)
            # Candidates as (value, precision). A percent also tries value/100,
            # which carries two MORE decimal places — critical so "5%" -> 0.05 is
            # compared at 2 dp and doesn't spuriously collide with near-zero values.
            cands = [(base, dec)]
            if pct:
                cands.append((base / 100.0, dec + 2))

            entry = {"token": token, "line_no": lineno,
                     "line": line.strip(), "ledger_paths": []}

            if in_p:
                entry["category"] = "p-threshold"
                results.append(entry)
                continue

            pre = preceding_word(line, start)
            if pre in STRUCTURAL_WORDS:
                entry["category"] = "structural"
                results.append(entry)
                continue

            # A percentage naming a convention ("5% level", "95% confidence
            # interval") is a cutoff, not a computed quantity.
            if pct and following_word(line, m.end()) in CONVENTION_FOLLOW:
                entry["category"] = "convention"
                results.append(entry)
                continue

            # Try to match against the ledger (percent tries both forms).
            hits = []
            for c, cdec in cands:
                hits = matches(c, known, cdec, tol)
                if hits:
                    break
            if hits:
                entry["category"] = "matched"
                entry["ledger_paths"] = sorted(set(hits))
            elif dec == 0 and 1900 <= base <= 2099:
                entry["category"] = "year?"
            else:
                entry["category"] = "ORPHAN"
            results.append(entry)
    return results


def main():
    ap = argparse.ArgumentParser(description="Reconcile report numbers against a results ledger.")
    ap.add_argument("--report", required=True, help="Path to the drafted report (markdown/text)")
    ap.add_argument("--ledger", required=True, help="Path to results.json (the analysis's numeric output)")
    ap.add_argument("--tol", type=float, default=0.0,
                    help="Absolute tolerance floor for a match (default: rounding-only)")
    ap.add_argument("--warn-only", action="store_true", help="Report but always exit 0")
    ap.add_argument("--show-matched", action="store_true", help="Also list matched numbers")
    args = ap.parse_args()

    try:
        ledger = json.load(open(args.ledger))
    except Exception as e:
        print(f"error: could not read ledger {args.ledger}: {e}", file=sys.stderr)
        sys.exit(2)
    try:
        report_text = open(args.report, encoding="utf-8").read()
    except Exception as e:
        print(f"error: could not read report {args.report}: {e}", file=sys.stderr)
        sys.exit(2)

    known = harvest_numbers(ledger)
    if not known:
        print(f"error: ledger {args.ledger} contains no numeric values", file=sys.stderr)
        sys.exit(2)

    results = classify_and_check(report_text, known, args.tol)
    cats = {}
    for r in results:
        cats.setdefault(r["category"], []).append(r)

    n = len(results)
    orphans = cats.get("ORPHAN", [])
    print(f"Reconciled {n} number(s) in {args.report} against {len(known)} ledger value(s):")
    print(f"  matched:      {len(cats.get('matched', []))}")
    print(f"  p-threshold:  {len(cats.get('p-threshold', []))}  (conventional cutoffs, not checked)")
    print(f"  convention:   {len(cats.get('convention', []))}  (e.g. 5% level, 95% CI)")
    print(f"  structural:   {len(cats.get('structural', []))}  (Table/Model/Section refs)")
    print(f"  year?:        {len(cats.get('year?', []))}  (look like years — verify if substantive)")
    print(f"  ORPHANS:      {len(orphans)}")

    if args.show_matched and cats.get("matched"):
        print("\n-- matched --")
        for r in cats["matched"]:
            print(f"  L{r['line_no']}: {r['token']:>12}  ->  {', '.join(r['ledger_paths'])}")

    if cats.get("year?"):
        print("\n-- looks like a year (verify if it's a substantive quantity) --")
        for r in cats["year?"]:
            print(f"  L{r['line_no']}: {r['token']}   | {r['line'][:90]}")

    if orphans:
        print("\n-- ORPHANS: numbers not found in the computed results (likely hand-typed/hallucinated) --")
        for r in orphans:
            print(f"  L{r['line_no']}: {r['token']}   | {r['line'][:90]}")
        print("\nEach orphan must be traced to a computed value (add it to the ledger) "
              "or removed/corrected. A number that exists only in prose is a red flag.")

    if orphans and not args.warn_only:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
