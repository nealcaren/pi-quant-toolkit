# Phase 1 — Acquire

Fetch the data through the source's API or a scripted call, land it in the
immutable raw zone, and capture provenance as you go. **Do not open the data to
clean, recode, or subset it** — that is the next skill's job.

## Tasks

### 1. Create the landing directory
```
data/raw/<dataset>/        # one folder per dataset, named for the source
```
Use a short, stable slug (e.g. `data/raw/gss-cumulative/`,
`data/raw/dvn-abc123/`). Everything for this dataset lives here.

### 2. Fetch through the source guide
Follow the matching `sources/*.md`:
- **Dataverse** → `sources/dataverse.md` (use `scripts/dataverse_get.py`).
- **IPUMS** → `sources/ipums.md` (API extract via `ipumsr` / `ipumspy`).
- **Census/ACS** → `sources/census_acs.md` (`tidycensus` / Census API).
- **GSS / ANES / ICPSR** → `sources/survey_archives.md`.
- **OSF / journal zip / bare URL** → `sources/replication_package.md`.

Prefer **original / un-reingested** file formats where the archive offers them
(e.g. Dataverse `format=original`) so variable labels and value labels survive.

### 3. Write provenance — `data/raw/<dataset>/PROVENANCE.md`
The scripted fetchers write most of this; fill any gaps by hand. Never invent a
field the source didn't provide — leave it blank.

```markdown
# Provenance: <dataset>

- **Source**: <installation / archive name>
- **Persistent ID**: <DOI / handle / study #>
- **Version**: <version + release date>
- **Retrieved**: <YYYY-MM-DD>
- **Retrieved via**: <exact API call / script command / manual step>
- **License / terms**: <license; restricted? DUA?>
- **Required citation**: <how the data must be cited>

## Files
| File | Bytes | Checksum (md5) | Notes |
|------|-------|----------------|-------|
| ...  | ...   | ...            | original format / ingested / codebook |
```

### 4. Capture the codebook
Save any codebook / data dictionary / DDI the source provides into
`data/codebooks/<dataset>/`. If the source provides none, note that in
`PROVENANCE.md` — do not reconstruct one from guesses.

### 5. Save the re-runnable acquisition script
Write the exact steps to `scripts/cleaning/00_acquire.(sh|R|py)` so the download
reproduces with one command. For manual-login sources, the script documents the
manual step and then verifies the file exists at the expected path.

- Python helpers use `uv` + PEP-723 inline dependencies (`uv run …`), per project
  convention — never bare `python`/`pip`. If the student doesn't have `uv`, offer
  to install it first (macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`;
  Windows PowerShell: `irm https://astral.sh/uv/install.ps1 | iex`).
- The `uv run …` command is identical on macOS and Windows. The wrapper script's
  extension is not: save it as `00_acquire.sh` (macOS/Linux) or `00_acquire.ps1`
  (Windows), or as `00_acquire.R` when the fetch is R (`ipumsr`/`tidycensus`/`gssr`).
- Include the resolved DOI/version, not a transient link.

### 6. Do **not** touch the data
No `read_csv() |> mutate()`, no re-saving as a "cleaned" copy, no dropping
columns. The only reads allowed here are the read-only checks in Phase 2.

## Output
Raw files + `PROVENANCE.md` + `MANIFEST.json` in `data/raw/<dataset>/`, codebook
in `data/codebooks/<dataset>/`, and `scripts/cleaning/00_acquire.*` committed.
