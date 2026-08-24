# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Read from and write to a LOCAL Zotero SQLite library directly.

USE WITH CARE. This writes straight into zotero.sqlite, bypassing Zotero's
data layer. To keep the library safe the `add` command will REFUSE to run
while Zotero is open (the DB is locked), and always takes a timestamped
backup of the database before its first write. After adding items you must
(re)start Zotero for them to appear; new items are flagged unsynced
(version=0, synced=0) so Zotero uploads them on its next sync.

Commands:
  collections            List collections (name -> key) in the user library.
  find --doi <DOI>       Report whether a DOI already exists (dedup helper).
  find --title <STR>     Case-insensitive title substring search.
  add --json <FILE|->    Insert one item from a JSON object (see schema below).

Add JSON schema (all fields optional except itemType + title):
  {
    "itemType": "journalArticle",          # Zotero type name
    "title": "...",
    "creators": [                            # in order
       {"firstName": "Jane", "lastName": "Smith"},
       {"name": "World Bank"}                # single-field (institution)
    ],
    "date": "2020-05-01",                    # or "2020"
    "DOI": "10.1093/sf/soaa001",
    "url": "https://...",
    "publicationTitle": "Social Forces",
    "volume": "99", "issue": "2", "pages": "1-30",
    "abstractNote": "...",
    "language": "en", "ISSN": "...",
    "tags": ["theory", "methods"],
    "collection": "My Reading List"          # existing collection NAME (optional)
  }

Exit codes: 0 ok; 2 Zotero is open / DB locked; 3 bad input; 4 other error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import sqlite3
import sys
from datetime import datetime, timezone

# Zotero object-key alphabet (no 0/1/I/O/… ambiguity), 8 chars.
KEY_ALPHABET = "23456789ABCDEFGHIJKLMNPQRSTUVWXYZ"
USER_LIBRARY_TYPE = "user"
AUTHOR_CREATOR_TYPE = "author"
DEFAULT_DB = os.path.expanduser("~/Zotero/zotero.sqlite")


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def err(msg: str, code: int = 4):
    print(msg, file=sys.stderr)
    sys.exit(code)


def connect(db_path: str, *, write: bool) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        err(f"No Zotero database at {db_path}. Pass --db with the correct path.", 3)
    # Immutable/RO for reads means we never disturb a running Zotero.
    if not write:
        uri = f"file:{db_path}?mode=ro&immutable=1"
        return sqlite3.connect(uri, uri=True, timeout=2)
    conn = sqlite3.connect(db_path, timeout=2)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def ensure_unlocked(conn: sqlite3.Connection):
    """Refuse to write while Zotero holds the database (prevents corruption)."""
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("ROLLBACK")
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower() or "busy" in str(e).lower():
            err(
                "Zotero appears to be OPEN (database is locked). Quit Zotero "
                "completely, then re-run. Writing while Zotero runs can corrupt "
                "the library.",
                2,
            )
        raise


def user_library_id(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT libraryID FROM libraries WHERE type=? ORDER BY libraryID LIMIT 1",
        (USER_LIBRARY_TYPE,),
    ).fetchone()
    return row[0] if row else 1


def backup_db(db_path: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = f"{db_path}.pi-backup-{stamp}"
    shutil.copy2(db_path, dest)
    for ext in ("-wal", "-shm"):
        if os.path.exists(db_path + ext):
            shutil.copy2(db_path + ext, dest + ext)
    return dest


# ---- lookups -------------------------------------------------------------

def item_type_id(conn, type_name: str) -> int:
    row = conn.execute(
        "SELECT itemTypeID FROM itemTypes WHERE typeName=?", (type_name,)
    ).fetchone()
    if not row:
        err(f"Unknown Zotero itemType '{type_name}'.", 3)
    return row[0]


def valid_fields_for_type(conn, type_id: int) -> dict[str, int]:
    rows = conn.execute(
        """SELECT f.fieldName, f.fieldID
           FROM itemTypeFieldsCombined itf
           JOIN fieldsCombined f ON f.fieldID=itf.fieldID
           WHERE itf.itemTypeID=?""",
        (type_id,),
    ).fetchall()
    return {name: fid for name, fid in rows}


def creator_type_id(conn, name: str) -> int:
    row = conn.execute(
        "SELECT creatorTypeID FROM creatorTypes WHERE creatorType=?", (name,)
    ).fetchone()
    return row[0] if row else 8  # author


def unique_key(conn, library_id: int) -> str:
    while True:
        key = "".join(secrets.choice(KEY_ALPHABET) for _ in range(8))
        exists = conn.execute(
            "SELECT 1 FROM items WHERE libraryID=? AND key=?", (library_id, key)
        ).fetchone()
        if not exists:
            return key


def multipart_date(raw: str) -> str:
    """Zotero stores date as 'YYYY-MM-DD <original string>' (00 for unknown)."""
    raw = str(raw).strip()
    m = re.match(r"^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", raw)
    if not m:
        # Non-parseable: store a null SQL prefix so Zotero keeps the raw string.
        return f"0000-00-00 {raw}"
    y = m.group(1)
    mo = f"{int(m.group(2)):02d}" if m.group(2) else "00"
    d = f"{int(m.group(3)):02d}" if m.group(3) else "00"
    return f"{y}-{mo}-{d} {raw}"


def value_id(conn, value: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO itemDataValues (value) VALUES (?)", (value,)
    )
    return conn.execute(
        "SELECT valueID FROM itemDataValues WHERE value=?", (value,)
    ).fetchone()[0]


def creator_id(conn, first: str, last: str, field_mode: int) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO creators (firstName, lastName, fieldMode) VALUES (?,?,?)",
        (first, last, field_mode),
    )
    return conn.execute(
        "SELECT creatorID FROM creators WHERE firstName=? AND lastName=? AND fieldMode=?",
        (first, last, field_mode),
    ).fetchone()[0]


# ---- commands ------------------------------------------------------------

def cmd_collections(args):
    conn = connect(args.db, write=False)
    lib = user_library_id(conn)
    rows = conn.execute(
        "SELECT collectionName, key FROM collections WHERE libraryID=? ORDER BY collectionName",
        (lib,),
    ).fetchall()
    for name, key in rows:
        print(f"{key}\t{name}")
    print(f"# {len(rows)} collections", file=sys.stderr)


def cmd_find(args):
    conn = connect(args.db, write=False)
    if args.doi:
        rows = conn.execute(
            """SELECT i.key, v.value FROM items i
               JOIN itemData d ON d.itemID=i.itemID
               JOIN fieldsCombined f ON f.fieldID=d.fieldID AND f.fieldName='DOI'
               JOIN itemDataValues v ON v.valueID=d.valueID
               WHERE lower(v.value)=lower(?)""",
            (args.doi,),
        ).fetchall()
        if rows:
            print(json.dumps({"exists": True, "keys": [r[0] for r in rows]}))
        else:
            print(json.dumps({"exists": False, "keys": []}))
        return
    if args.title:
        rows = conn.execute(
            """SELECT i.key, v.value FROM items i
               JOIN itemData d ON d.itemID=i.itemID
               JOIN fieldsCombined f ON f.fieldID=d.fieldID AND f.fieldName='title'
               JOIN itemDataValues v ON v.valueID=d.valueID
               WHERE lower(v.value) LIKE lower(?) LIMIT 25""",
            (f"%{args.title}%",),
        ).fetchall()
        print(json.dumps([{"key": k, "title": t} for k, t in rows], indent=2))
        return
    err("find needs --doi or --title", 3)


def load_item(spec: str) -> dict:
    text = sys.stdin.read() if spec == "-" else open(spec, encoding="utf-8").read()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        err(f"Bad JSON: {e}", 3)
    if not obj.get("title"):
        err("Item needs a 'title'.", 3)
    return obj


def cmd_add(args):
    obj = load_item(args.json)
    conn = connect(args.db, write=True)
    ensure_unlocked(conn)

    if not args.no_backup:
        dest = backup_db(args.db)
        print(f"Backed up database -> {dest}", file=sys.stderr)

    lib = user_library_id(conn)
    type_name = obj.get("itemType") or "journalArticle"
    tid = item_type_id(conn, type_name)
    valid = valid_fields_for_type(conn, tid)

    try:
        conn.execute("BEGIN IMMEDIATE")
        key = unique_key(conn, lib)
        ts = now_utc()
        cur = conn.execute(
            """INSERT INTO items
               (itemTypeID, dateAdded, dateModified, clientDateModified,
                libraryID, key, version, synced)
               VALUES (?,?,?,?,?,?,0,0)""",
            (tid, ts, ts, ts, lib, key),
        )
        item_id = cur.lastrowid

        skipped = []
        for field, raw in obj.items():
            if field in ("itemType", "creators", "tags", "collection"):
                continue
            if raw in (None, "", []):
                continue
            if field not in valid:
                skipped.append(field)
                continue
            value = multipart_date(raw) if field == "date" else str(raw)
            vid = value_id(conn, value)
            conn.execute(
                "INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?,?,?)",
                (item_id, valid[field], vid),
            )

        # creators
        for order, c in enumerate(obj.get("creators") or []):
            if c.get("name"):
                cid = creator_id(conn, "", str(c["name"]).strip(), 1)
            else:
                first = str(c.get("firstName", "") or "").strip()
                last = str(c.get("lastName", "") or "").strip()
                if not last and not first:
                    continue
                cid = creator_id(conn, first, last or first, 0)
            ctype = creator_type_id(conn, c.get("creatorType", AUTHOR_CREATOR_TYPE))
            conn.execute(
                """INSERT INTO itemCreators
                   (itemID, creatorID, creatorTypeID, orderIndex) VALUES (?,?,?,?)""",
                (item_id, cid, ctype, order),
            )

        # tags
        for tag in obj.get("tags") or []:
            tag = str(tag).strip()
            if not tag:
                continue
            conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
            tag_id = conn.execute(
                "SELECT tagID FROM tags WHERE name=?", (tag,)
            ).fetchone()[0]
            conn.execute(
                "INSERT OR IGNORE INTO itemTags (itemID, tagID, type) VALUES (?,?,0)",
                (item_id, tag_id),
            )

        # collection
        coll_note = ""
        if obj.get("collection"):
            row = conn.execute(
                "SELECT collectionID FROM collections WHERE libraryID=? AND collectionName=?",
                (lib, obj["collection"]),
            ).fetchone()
            if row:
                nxt = conn.execute(
                    "SELECT COALESCE(MAX(orderIndex)+1,0) FROM collectionItems WHERE collectionID=?",
                    (row[0],),
                ).fetchone()[0]
                conn.execute(
                    "INSERT OR IGNORE INTO collectionItems (collectionID, itemID, orderIndex) VALUES (?,?,?)",
                    (row[0], item_id, nxt),
                )
            else:
                coll_note = f" (collection '{obj['collection']}' not found; left in library root)"

        # integrity check before we commit anything
        problems = conn.execute("PRAGMA foreign_key_check").fetchall()
        if problems:
            conn.execute("ROLLBACK")
            err(f"Aborted: foreign-key check failed: {problems}", 4)

        conn.execute("COMMIT")
    except Exception as e:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        err(f"Insert failed, rolled back: {e}", 4)

    result = {"ok": True, "key": key, "itemType": type_name, "title": obj["title"]}
    if skipped:
        result["skipped_fields"] = skipped
    print(json.dumps(result) + coll_note)


def main():
    p = argparse.ArgumentParser(description="Direct read/write for a local Zotero library.")
    p.add_argument("--db", default=DEFAULT_DB, help=f"Path to zotero.sqlite (default {DEFAULT_DB})")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("collections").set_defaults(func=cmd_collections)

    f = sub.add_parser("find")
    f.add_argument("--doi")
    f.add_argument("--title")
    f.set_defaults(func=cmd_find)

    a = sub.add_parser("add")
    a.add_argument("--json", required=True, help="Path to a JSON item, or '-' for stdin")
    a.add_argument("--no-backup", action="store_true", help="Skip the pre-write backup (not advised)")
    a.set_defaults(func=cmd_add)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
