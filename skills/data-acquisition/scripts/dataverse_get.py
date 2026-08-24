# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31"]
# ///
"""
dataverse_get.py — list and download Dataverse datasets reproducibly.

Works with ANY Dataverse installation (Harvard is the default). Given a DOI or a
dataset URL, it reads the dataset's file metadata, then either prints a manifest
or downloads the files into an immutable raw folder with a PROVENANCE.md and a
MANIFEST.json (checksums included).

Design choices that matter for reproducibility:
  * Pins a version. Dataverse datasets are revised; you record which one.
  * Fetches the ORIGINAL upload for ingested tabular files (.dta/.sav/.csv/...).
    Dataverse "ingests" tabular files and serves a derived .tab by default, which
    strips the original format and value labels. --originals (default on) asks
    for `?format=original` so labels survive.
  * Verifies md5 checksums for non-ingested files. For ingested files the stored
    md5 is of the derived .tab, not the original we download, so we record but do
    not claim to verify — and say so, rather than implying a check that didn't run.
  * Never fabricates. Missing metadata fields are left blank.

Usage (run with uv, per project convention):
  # List what's in a dataset without downloading:
  uv run dataverse_get.py manifest "doi:10.7910/DVN/ABC123"

  # Download everything (latest version) into data/raw/:
  uv run dataverse_get.py get "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/ABC123" \
      --out data/raw/dvn-abc123

  # Pin a version, only some files, restricted dataset with a token:
  uv run dataverse_get.py get "doi:10.7910/DVN/ABC123" --version 2.1 \
      --include "*.dta" --out data/raw/dvn-abc123 --token "$DATAVERSE_API_TOKEN"

The API token (for restricted files) may also come from the DATAVERSE_API_TOKEN
env var. Never hardcode it.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import requests

DEFAULT_SERVER = "https://dataverse.harvard.edu"

# Some Dataverse installations sit behind a CDN/WAF that 403s the default
# python-requests User-Agent. Present a normal one.
USER_AGENT = "pi-quant-toolkit-data-acquisition/1.0 (+https://github.com/nealcaren/pi-quant-toolkit)"


def hdrs(token: str | None) -> dict:
    h = {"User-Agent": USER_AGENT}
    if token:
        h["X-Dataverse-key"] = token
    return h


def eprint(*a):
    print(*a, file=sys.stderr)


def resolve_pid_and_server(target: str, server: str | None) -> tuple[str, str]:
    """Accept a raw DOI ('doi:10.7910/DVN/ABC'), a bare DOI, or a dataset URL.
    Returns (persistentId, server_base_url)."""
    target = target.strip()
    if target.startswith("http://") or target.startswith("https://"):
        u = urlparse(target)
        base = f"{u.scheme}://{u.netloc}"
        qs = parse_qs(u.query)
        if "persistentId" in qs:
            return qs["persistentId"][0], (server or base)
        # doi.org style: https://doi.org/10.7910/DVN/ABC -> needs an explicit server
        if u.netloc.endswith("doi.org"):
            pid = "doi:" + u.path.lstrip("/")
            if not server:
                eprint("A doi.org URL needs --server (the Dataverse installation). "
                       f"Defaulting to {DEFAULT_SERVER}.")
            return pid, (server or DEFAULT_SERVER)
        eprint("Could not find persistentId in URL; pass the DOI directly.")
        sys.exit(2)
    # Looks like a DOI/handle
    if not (target.startswith("doi:") or target.startswith("hdl:")):
        if target.startswith("10."):
            target = "doi:" + target
    return target, (server or DEFAULT_SERVER)


def fetch_version(server: str, pid: str, version: str, token: str | None) -> dict:
    """Fetch dataset version metadata (files + version info)."""
    headers = hdrs(token)
    if version and version != ":latest-published":
        url = f"{server}/api/datasets/:persistentId/versions/{version}"
    else:
        # :latest-published is the safe default for reproducibility
        url = f"{server}/api/datasets/:persistentId/versions/:latest-published"
    r = requests.get(url, params={"persistentId": pid}, headers=headers, timeout=60)
    if r.status_code == 404:
        eprint(f"Dataset or version not found: {pid} (version={version}) on {server}")
        sys.exit(3)
    r.raise_for_status()
    payload = r.json()
    if payload.get("status") != "OK":
        eprint("Dataverse API returned non-OK:", payload.get("message", payload))
        sys.exit(3)
    return payload["data"]


def file_records(version_data: dict) -> list[dict]:
    """Normalize the file list into simple records."""
    out = []
    for f in version_data.get("files", []):
        df = f.get("dataFile", {})
        checksum = df.get("checksum", {}) or {}
        directory = f.get("directoryLabel", "")
        label = f.get("label") or df.get("filename", "")
        ingested = bool(df.get("originalFileFormat")) or bool(df.get("originalFileName"))
        out.append({
            "id": df.get("id"),
            "filename": label,
            "directoryLabel": directory,
            "contentType": df.get("contentType", ""),
            "filesize": df.get("filesize"),
            "md5": df.get("md5") or (checksum.get("value") if checksum.get("type", "").lower() == "md5" else None),
            "checksumType": (checksum.get("type") or ("MD5" if df.get("md5") else "")),
            "checksumValue": checksum.get("value") or df.get("md5"),
            "ingested": ingested,
            "originalFileName": df.get("originalFileName"),
            "restricted": bool(f.get("restricted")),
        })
    return out


def matches(name: str, include: list[str], exclude: list[str]) -> bool:
    if include and not any(fnmatch.fnmatch(name, p) for p in include):
        return False
    if exclude and any(fnmatch.fnmatch(name, p) for p in exclude):
        return False
    return True


def human(n) -> str:
    if not isinstance(n, (int, float)):
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def _stream_to(path: str, params: dict, url: str, headers: dict):
    """Stream one URL to path, returning (status, bytes, md5hex, sha256hex).
    status is 'ok', or the HTTP code as an int on a non-2xx that we handle."""
    with requests.get(url, params=params, headers=headers, stream=True, timeout=300) as r:
        if r.status_code >= 400:
            return r.status_code, 0, None, None
        md5 = hashlib.md5()
        sha = hashlib.sha256()
        size = 0
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
                md5.update(chunk)
                sha.update(chunk)
                size += len(chunk)
    return "ok", size, md5.hexdigest(), sha.hexdigest()


def download_file(server: str, rec: dict, dest_dir: str, originals: bool,
                  token: str | None) -> dict:
    """Download one datafile. Returns a manifest entry with actual sha256/md5.
    Falls back gracefully: original -> archival if the original object is missing
    (some ingested files have no separate original on storage)."""
    headers = hdrs(token)
    url = f"{server}/api/access/datafile/{rec['id']}"
    want_original = originals and rec["ingested"]

    # Preserve the archive's directory structure and use the original filename
    # for ingested files so labels/format are unambiguous.
    subdir = rec.get("directoryLabel") or ""

    def paths_for(as_original: bool):
        name = rec["originalFileName"] if as_original and rec.get("originalFileName") else rec["filename"]
        base = os.path.join(dest_dir, subdir) if subdir else dest_dir
        return os.path.join(base, name), name

    # Attempt list: try original first when wanted, then archival.
    attempts = [True, False] if want_original else [False]
    fell_back = False
    for as_original in attempts:
        path, out_name = paths_for(as_original)
        params = {"format": "original"} if as_original else {}
        status, size, md5hex, shahex = _stream_to(path, params, url, headers)
        if status == "ok":
            got_original = as_original
            break
        if status in (401, 403):
            eprint(f"  ! restricted (need a token/permission): {out_name} [{status}]")
            return {"filename": out_name, "downloaded": False,
                    "reason": f"http {status} (restricted)"}
        if as_original and False in attempts[attempts.index(as_original) + 1:]:
            eprint(f"  ~ original not available for {out_name} [{status}]; using archival format")
            fell_back = True
            continue
        eprint(f"  ! download failed: {out_name} [http {status}]")
        return {"filename": out_name, "downloaded": False, "reason": f"http {status}"}

    entry = {
        "filename": os.path.relpath(path, dest_dir),
        "downloaded_format": "original" if got_original else "archival/native",
        "bytes": size,
        "md5_downloaded": md5hex,
        "sha256_downloaded": shahex,
        "md5_reported_by_dataverse": rec.get("checksumValue"),
    }
    if fell_back:
        entry["fell_back_to_archival"] = True
    # Verify md5 ONLY for non-ingested files. For ingested tabular files the
    # referent of Dataverse's reported checksum (original upload vs. derived .tab)
    # is ambiguous across Dataverse versions, so comparing it to the served bytes
    # produces false mismatches. We record the reported value but do not claim a
    # check — a false "MISMATCH, do not use" on good data is worse than no check.
    if rec["ingested"]:
        entry["md5_verified"] = None
        entry["note"] = ("ingested tabular file; Dataverse's reported checksum referent "
                         "is ambiguous for ingested files, so it is recorded but not verified. "
                         "Verify against the dataset's own codebook/README if integrity is critical.")
    elif rec.get("checksumType", "").upper() == "MD5" and rec.get("checksumValue"):
        entry["md5_verified"] = (md5hex.lower() == rec["checksumValue"].lower())
        if entry["md5_verified"] is False:
            eprint(f"  ! CHECKSUM MISMATCH: {entry['filename']}")
    else:
        entry["md5_verified"] = None
        entry["note"] = "no comparable md5 reported by source"
    return entry


def write_provenance(dest_dir: str, server: str, pid: str, version_data: dict,
                     manifest: list[dict]):
    vnum = version_data.get("versionNumber")
    vminor = version_data.get("versionMinorNumber")
    version_str = f"{vnum}.{vminor}" if vnum is not None else "(unpublished/draft)"
    release = version_data.get("releaseTime", "")
    retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# Provenance: {pid}",
        "",
        f"- **Source**: Dataverse ({server})",
        f"- **Persistent ID**: {pid}",
        f"- **Version**: {version_str}" + (f"  (released {release})" if release else ""),
        f"- **Retrieved**: {retrieved} (UTC)",
        f"- **Retrieved via**: dataverse_get.py against {server}/api/access/datafile/…",
        "- **License / terms**: see the dataset page; verify before redistributing",
        f"- **Required citation**: cite the dataset by its DOI ({pid}) and version {version_str}",
        "",
        "## Files",
        "| File | Bytes | Format | md5 (downloaded) | md5 verified |",
        "|------|-------|--------|------------------|--------------|",
    ]
    for m in manifest:
        if not m.get("downloaded", True):
            lines.append(f"| {m.get('filename','?')} | — | — | — | NOT DOWNLOADED ({m.get('reason')}) |")
            continue
        verified = m.get("md5_verified")
        vtxt = {True: "yes", False: "**MISMATCH**", None: "n/a — " + m.get("note", "")}[verified]
        lines.append(f"| {m['filename']} | {m['bytes']} | {m['downloaded_format']} | "
                     f"`{m['md5_downloaded']}` | {vtxt} |")
    lines += ["", "_Generated by dataverse_get.py. Do not edit files in this folder; "
              "raw data is immutable (see data-acquisition skill)._", ""]
    with open(os.path.join(dest_dir, "PROVENANCE.md"), "w") as fh:
        fh.write("\n".join(lines))

    with open(os.path.join(dest_dir, "MANIFEST.json"), "w") as fh:
        json.dump({
            "source": "dataverse",
            "server": server,
            "persistentId": pid,
            "version": version_str,
            "releaseTime": release,
            "retrieved_utc": retrieved,
            "files": manifest,
        }, fh, indent=2)


def cmd_manifest(args):
    pid, server = resolve_pid_and_server(args.target, args.server)
    token = args.token or os.environ.get("DATAVERSE_API_TOKEN")
    vdata = fetch_version(server, pid, args.version, token)
    recs = file_records(vdata)
    vnum = vdata.get("versionNumber")
    vminor = vdata.get("versionMinorNumber")
    print(f"# {pid}  on {server}")
    print(f"# version {vnum}.{vminor}  released {vdata.get('releaseTime','')}")
    print(f"# {len(recs)} file(s)\n")
    total = 0
    for r in recs:
        total += r["filesize"] or 0
        flags = []
        if r["restricted"]:
            flags.append("RESTRICTED")
        if r["ingested"]:
            flags.append("ingested→use --originals")
        path = (r["directoryLabel"] + "/" if r["directoryLabel"] else "") + r["filename"]
        print(f"  {human(r['filesize']):>8}  {path}"
              + (f"   [{', '.join(flags)}]" if flags else ""))
    print(f"\n# total ~{human(total)}")


def cmd_get(args):
    pid, server = resolve_pid_and_server(args.target, args.server)
    token = args.token or os.environ.get("DATAVERSE_API_TOKEN")
    vdata = fetch_version(server, pid, args.version, token)
    recs = file_records(vdata)

    include = args.include or []
    exclude = args.exclude or []
    selected = [r for r in recs if matches(r["filename"], include, exclude)]
    if not selected:
        eprint("No files matched the include/exclude filters.")
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    eprint(f"Downloading {len(selected)} file(s) from {pid} → {args.out}")
    manifest = []
    for r in selected:
        if r["restricted"] and not token:
            eprint(f"  ! {r['filename']} is restricted and no token was given; skipping.")
            manifest.append({**r, "downloaded": False, "reason": "restricted, no token"})
            continue
        eprint(f"  · {r['filename']} ({human(r['filesize'])})"
               + ("  [original]" if (args.originals and r['ingested']) else ""))
        try:
            manifest.append(download_file(server, r, args.out, args.originals, token))
        except Exception as e:  # keep the batch alive; record the failure
            eprint(f"  ! error downloading {r['filename']}: {e}")
            manifest.append({"filename": r["filename"], "downloaded": False,
                             "reason": f"exception: {e}"})

    write_provenance(args.out, server, pid, vdata, manifest)
    n_ok = sum(1 for m in manifest if m.get("downloaded", True))
    n_bad = sum(1 for m in manifest if m.get("md5_verified") is False)
    eprint(f"Done. {n_ok} file(s) written. PROVENANCE.md + MANIFEST.json in {args.out}")
    if n_bad:
        eprint(f"WARNING: {n_bad} checksum mismatch(es) — do not use until resolved.")
        sys.exit(4)


def main():
    p = argparse.ArgumentParser(description="List/download Dataverse datasets reproducibly.")
    p.add_argument("--server", help=f"Dataverse base URL (default {DEFAULT_SERVER} or inferred from a URL)")
    p.add_argument("--version", default=":latest-published",
                   help="Version to pin, e.g. '2.1' (default: latest published)")
    p.add_argument("--token", help="API token for restricted files (or env DATAVERSE_API_TOKEN)")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("manifest", help="List files without downloading")
    m.add_argument("target", help="DOI ('doi:10.7910/DVN/…') or dataset URL")
    m.set_defaults(func=cmd_manifest)

    g = sub.add_parser("get", help="Download files")
    g.add_argument("target", help="DOI ('doi:10.7910/DVN/…') or dataset URL")
    g.add_argument("--out", required=True, help="Destination dir, e.g. data/raw/dvn-abc123")
    g.add_argument("--include", nargs="*", help="Only files matching these glob(s), e.g. '*.dta'")
    g.add_argument("--exclude", nargs="*", help="Skip files matching these glob(s)")
    g.add_argument("--no-originals", dest="originals", action="store_false",
                   help="Download the derived/archival format instead of original uploads")
    g.set_defaults(func=cmd_get, originals=True)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
