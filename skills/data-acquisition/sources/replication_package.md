# OSF, journal supplements, and generic archives

For replication data that isn't on a first-class source above: OSF projects,
journal "supplementary material" zips, or a bare file URL. Try to resolve the DOI
first — a surprising share of these actually live on Dataverse (use
`sources/dataverse.md`).

Commands are given for both **macOS/Linux** (`curl`) and **Windows PowerShell**
(`Invoke-WebRequest`).

## OSF (Open Science Framework)

OSF has a public API. Every file and folder has a stable URL.

- A project is `https://osf.io/<id>/`. Files are downloadable at
  `https://osf.io/<id>/download` (append `/download` to a file's short URL).
- Whole-component archive: `https://files.osf.io/v1/resources/<id>/providers/osfstorage/?zip=`

```bash
# macOS / Linux — one file
curl -L "https://osf.io/abcde/download" -o data/raw/osf-project/data.csv
```
```powershell
# Windows PowerShell — one file
Invoke-WebRequest "https://osf.io/abcde/download" -OutFile data/raw/osf-project/data.csv
```

For many files, the `osfclient` tool (`uv run --with osfclient osf -p <id> clone`)
mirrors a whole project — offer it if the package is large. (`uv` install: see
`sources/dataverse.md`.)

## Dataverse whole-dataset zip (uv-free fallback)

If the student can't install `uv`, grab the entire Dataverse dataset as one zip:

```bash
# macOS / Linux
curl -L "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/ABC123" \
     -o data/raw/dvn-abc123/dataset.zip
```
```powershell
# Windows PowerShell
Invoke-WebRequest "https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/ABC123" -OutFile data/raw/dvn-abc123/dataset.zip
```

Swap the server for other installations. You lose per-file `format=original`
handling and automatic checksum verification — so prefer the `uv` helper in
`sources/dataverse.md` when possible.

## Journal supplement / bare URL

```bash
# macOS / Linux
curl -L "<url-to-the-zip-or-file>" -o data/raw/<dataset>/<filename>
```
```powershell
# Windows PowerShell
Invoke-WebRequest "<url>" -OutFile data/raw/<dataset>/<filename>
```

## After any of these

1. If it's a zip, unpack **into** `data/raw/<dataset>/` and keep the original zip
   too (it's part of the provenance).
2. Compute a checksum for each file and record it in `PROVENANCE.md` /
   `MANIFEST.json` (nothing else generated one for you here).
3. Note the source URL, retrieval date, and any license the package states. A
   bare URL is weak provenance — capture whatever citation the package includes.
4. Save any codebook/README into `data/codebooks/<dataset>/`.
5. Do not edit the files; proceed to Phase 2.

Compute checksums:
```bash
# macOS / Linux
shasum -a 256 data/raw/<dataset>/* > data/raw/<dataset>/sha256.txt
```
```powershell
# Windows PowerShell
Get-FileHash data\raw\<dataset>\* -Algorithm SHA256 | Format-List
```
