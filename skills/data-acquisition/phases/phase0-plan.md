# Phase 0 — Plan the acquisition

Before downloading anything, establish exactly *what* you are getting so the
acquisition is reproducible and legal. Do not fetch large or restricted data
until the user confirms.

## Tasks

### 1. Resolve the source and persistent identifier
- Get the DOI, handle, study number, or URL from the user.
- Resolve it to a concrete source using the router in `SKILL.md`. A DOI usually
  resolves to a Dataverse installation — follow the redirect and note the server
  (e.g. `dataverse.harvard.edu`, `dataverse.unc.edu`, `data.qdr.syr.edu`).
- Record the **persistent ID**, not just a download link. Links rot; DOIs don't.

### 2. Pin the version
- Datasets get revised. Identify the version you intend to use (Dataverse and
  ICPSR both version; ACS/GSS/ANES have dated releases and cumulative vs.
  single-year files).
- Default to the **latest published** version unless the user is replicating a
  specific paper — then pin the version that paper used, if discoverable.
- Write the version down now; it goes in provenance.

### 3. Check access terms
- Is it open, or restricted / behind a login / under a Data Use Agreement?
- If restricted: tell the user what's required (registration, DUA, IRB, a data
  enclave). **Do not attempt to bypass authentication.** Ask whether they have
  credentials and how they want to proceed.
- Note the license / required citation. Journal replication archives require you
  to cite the data by its DOI and version.

### 4. Decide the scope
- Whole dataset, or specific files? For a replication package, usually the whole
  thing. For ACS/IPUMS, define the exact extract (geography, years, variables) —
  over-pulling wastes time and money and clutters the archive.
- Estimate size. If it's large (multi-GB microdata), confirm before pulling and
  plan `.gitignore` from the start.

## Output — a short acquisition plan

Confirm with the user before Phase 1:

```
Source:        <installation / archive>
Persistent ID: <DOI / handle / study #>
Version:       <version + release date>
Access:        open | restricted (<what's needed>)
Scope:         <whole dataset | file list | extract definition>
Est. size:     <MB/GB>
Lands at:      data/raw/<dataset>/
```

> **Pause.** Get user confirmation before downloading anything large or restricted.
