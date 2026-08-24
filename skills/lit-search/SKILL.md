---
name: lit-search
description: Find scholarship on a topic via OpenAlex and Crossref and add the chosen works straight into the user's local Zotero library (by writing zotero.sqlite directly). Use when the user wants to search the literature and capture references (NOT to screen, annotate, or synthesize them). Adding items requires Zotero to be closed.
---

# Literature Search → Zotero

You help a researcher find relevant scholarship through the OpenAlex API and
save the works they choose directly into their **local Zotero library**. This
is a *search-and-capture* workflow: find candidate papers, let the user pick,
add them to Zotero. It does NOT screen, annotate, or synthesize — stop once the
references are in Zotero.

## What you need

- **OpenAlex** — free, no key required; best for discovery (search, citation
  networks, topics, OA links). See `api/openalex-reference.md`.
- **Crossref** — free, no key required; best for authoritative publisher
  metadata for a known DOI (clean author names, venue, volume/issue/pages, ISSN,
  funders). See `api/crossref-reference.md`, including its Crossref→Zotero field
  map. Use it to enrich a work before adding it to Zotero; fall back to OpenAlex
  values when Crossref lacks a field.
- **The local Zotero database.** This skill writes references straight into
  `zotero.sqlite` via `scripts/zotero_db.py`. Because it writes to the database
  file directly, **Zotero must be CLOSED while adding items** — the script
  refuses to write while Zotero is open (the DB is locked) and always takes a
  timestamped backup before its first write. New items appear the next time the
  user opens Zotero and are flagged unsynced so Zotero uploads them on sync.
  Default DB path is `~/Zotero/zotero.sqlite`; pass `--db <path>` if theirs
  differs.

  All Zotero interaction is via the `bash` tool running that script:
  - `uv run scripts/zotero_db.py collections` — list collection names (read-only).
  - `uv run scripts/zotero_db.py find --doi <DOI>` — dedup check (read-only, safe
    while Zotero is open).
  - `uv run scripts/zotero_db.py add --json <file|->` — insert one item (needs
    Zotero closed).

## Workflow

### Phase 0: Scope

Read `phases/phase0-scope.md` and follow it. Briefly: clarify the topic, develop
search terms (synonyms, field vocabulary), and set date/language/type filters.
Confirm the search strategy with the user before querying.

Ask up front:
- **Topic** — a short description plus any specific terms the field uses.
- **Scope** — date range, particular journals or authors to prioritize, any
  methodological or geographic focus.
- **Which Zotero collection to file into** (optional). Run
  `uv run scripts/zotero_db.py collections` to list existing collection names,
  and confirm one with the user (or leave results in the library root). The
  chosen name is passed as `collection` in each item's JSON. The collection must
  already exist — the script won't create one.

### Phase 1: Search

Read `phases/phase1-search.md` and follow it. Run OpenAlex queries, retrieve
metadata (title, authors, year, journal, DOI, abstract, cited-by count),
deduplicate, and present the corpus to the user as a numbered list with year,
venue, and citation count so they can judge relevance at a glance.

Do **not** auto-screen or auto-exclude. The user decides what to keep — your job
is to surface candidates clearly.

### Phase 2: Add to Zotero

Once the user says which works to keep (e.g. "add 1, 3, and 7" or "add all"):

1. **Confirm Zotero is closed.** Tell the user to quit Zotero completely before
   you add anything — the script writes to the database file directly and will
   refuse (exit code 2) while Zotero is open.
2. **Optionally dedup** each candidate first with
   `uv run scripts/zotero_db.py find --doi <DOI>` and skip ones already present.
   For each kept work that has a DOI, fetch its Crossref record first
   (`api/crossref-reference.md`) and prefer that clean publisher metadata,
   falling back to OpenAlex for anything Crossref is missing.
3. **Build one JSON object per work** from the (Crossref-enriched) metadata and add it with
   `uv run scripts/zotero_db.py add --json -` (pipe the JSON on stdin), one call
   per work so a single bad record can't sink the batch. Fields:
   - `itemType` — usually `"journalArticle"`; use `"book"`, `"bookSection"`,
     `"conferencePaper"`, `"preprint"`, or `"report"` when the OpenAlex `type`
     indicates it.
   - `title`; `creators` — array of `{"firstName","lastName"}` (split OpenAlex
     author display names), or `{"name"}` for an organization, **in author
     order**; `date`; `DOI` (bare); `url`; `publicationTitle` (venue); `volume`;
     `issue`; `pages`; `abstractNote`; `tags` (optional); `collection` (the name
     from Phase 0, if any).

The script prints a JSON result with the new item `key` (and any `skipped_fields`).
After the batch, confirm to the user how many were saved, list any failures, and
tell them they can reopen Zotero to see the new references. Then stop — capture
is done and the user drives what happens next.

## Reminders

- **The user is the expert on relevance.** Present, don't pre-filter.
- **Never fabricate a DOI or metadata.** Add only what OpenAlex actually returns;
  leave a field blank if it's missing rather than guessing.
- **One work per `zotero_add` call**, so a single bad record doesn't sink the batch.
- This skill ends at capture. If the user later wants annotation or synthesis,
  that's a separate task.
