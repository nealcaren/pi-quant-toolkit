# Dataverse

Dataverse is where most social-science **replication packages** live. Harvard
Dataverse (`dataverse.harvard.edu`) is the largest, but the software is federated
— hundreds of installations exist (`dataverse.unc.edu`, `data.qdr.syr.edu`,
university and journal repositories). The API below works the same on all of them;
you just point at a different server.

A paper's "replication data" DOI almost always resolves to a Dataverse dataset,
even when the journal page links elsewhere. **Resolve the DOI first.**

## Prerequisite: uv

The bundled helper runs on **`uv`** (a fast Python runner). Check for it, and if
it's missing, offer to install it — don't make the student figure it out.

```bash
uv --version    # if this prints a version, you're set
```

If `uv` is not found, install it (one line, no admin needed), then retry:

- **macOS / Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows (PowerShell):** `irm https://astral.sh/uv/install.ps1 | iex`

After installing, open a new terminal (or `source ~/.bashrc` / `source ~/.zshrc`)
so `uv` is on the PATH. Then re-run `uv --version` to confirm. `uv run` pulls the
script's dependencies automatically the first time — nothing else to install.

> If the user can't or won't install `uv`, fall back to `sources/replication_package.md`,
> which uses the whole-dataset zip endpoint via `curl` (no Python). You lose the
> per-file `format=original` handling and checksum verification, so prefer `uv`.

## Step 1 — see what's in the dataset (no download)

```bash
uv run skills/data-acquisition/scripts/dataverse_get.py manifest \
    "doi:10.7910/DVN/ABC123"
```

- Accepts a bare DOI, `doi:…`, or a full dataset URL
  (`…/dataset.xhtml?persistentId=doi:…`). A `doi.org` URL needs `--server`.
- For a non-Harvard installation, add `--server https://dataverse.unc.edu`
  (auto-inferred when you pass a full dataset URL).
- The manifest flags **RESTRICTED** files and **ingested** tabular files.

## Step 2 — download into the immutable raw folder

```bash
uv run skills/data-acquisition/scripts/dataverse_get.py get \
    "doi:10.7910/DVN/ABC123" \
    --out data/raw/dvn-abc123
```

This writes the files, a `PROVENANCE.md`, and a `MANIFEST.json` (with checksums)
into `data/raw/dvn-abc123/`. Common options:

- `--version 2.1` — **pin a version.** Default is the latest *published* version.
  When replicating a specific paper, pin the version that paper used.
- `--include "*.dta" "*.do"` / `--exclude "*.pdf"` — glob filters.
- `--no-originals` — download Dataverse's derived/archival format instead of the
  original uploads (rarely what you want; see the ingest note below).
- `--token "$DATAVERSE_API_TOKEN"` — for restricted files (see below).

## The ingest gotcha (important)

When you upload a `.dta`, `.sav`, `.csv`, or `.xlsx`, Dataverse **"ingests"** it:
it stores a derived, tab-delimited `.tab` archival copy and serves *that* by
default. The `.tab` **loses the original format and often the variable/value
labels** — which you need for a labeled survey dataset.

The helper defaults to `--originals`, requesting `?format=original` so you get the
exact file the author uploaded (labels intact). Leave this on unless you have a
specific reason not to.

Checksum consequence: for **ingested** files, Dataverse's reported checksum
referent (the original upload vs. the derived `.tab`) is ambiguous across
Dataverse versions, so the helper **records** the reported md5 but marks
verification `n/a` — it will not fire a false "mismatch" on good data. **Non-ingested**
files (a `.zip`, `.do`, `.R`, `.pdf`) have a single stored object, so those *are*
verified against the reported md5, and a real mismatch stops the run with a
warning. Some ingested files also have no separate `original` object on storage;
the helper detects the 404 and transparently falls back to the archival format,
noting it in the manifest.

## Restricted files

If the manifest shows RESTRICTED, the file needs permission plus an API token:

1. The user logs in to the Dataverse installation → account → **API Token** →
   *Create Token*.
2. They must already have been granted access to the restricted file (request it
   on the dataset page; the depositor approves).
3. Provide the token via `--token` or, better, the `DATAVERSE_API_TOKEN` env var
   so it never lands in a script or the shell history.

**Do not attempt to bypass a restriction.** If access isn't granted, report that
to the user and stop.

## Whole-dataset zip (no per-file control)

For a quick grab of everything, Dataverse also serves the whole dataset as one
zip. The helper's per-file mode is preferred (originals + checksums), but the zip
is the fallback documented in `sources/replication_package.md`.

## After downloading

- Save any codebook/README PDF the package includes into
  `data/codebooks/<dataset>/`.
- Record the exact `uv run … get …` command in `scripts/cleaning/00_acquire.sh`.
- Proceed to Phase 2 (verify checksums, sanity-check shape, gitignore if large/
  restricted).
- Do **not** open the `.dta`/`.csv` to clean it — that's `r-analyst` /
  `stata-analyst` phase 1.
