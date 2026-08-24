# Crossref API Reference

Crossref is the DOI registration agency for most scholarly journals. Use it
alongside OpenAlex: OpenAlex is best for **discovery** (search, citation
networks, topics, OA links); Crossref is best for **authoritative
publisher-deposited metadata** for a known work — exact author given/family
names, container title, volume/issue/page, ISSN, funders, and license. When the
two disagree on a bibliographic field, Crossref reflects what the publisher
deposited, which is usually what belongs in a reference.

**Base URL**: `https://api.crossref.org`

**No authentication required.** Add a `mailto` to join the faster, more reliable
"polite pool":

```
https://api.crossref.org/works/10.1093/sf/soaa001?mailto=you@example.edu
```

Send a descriptive `User-Agent` including the mailto when scripting, e.g.
`pi-quant-toolkit/0.1 (mailto:you@example.edu)`.

## Core Endpoints

### Look up one work by DOI (the workhorse)

```
GET /works/{doi}
```

Returns `message` with the full metadata record. Example fields:

```jsonc
{
  "message": {
    "DOI": "10.1093/sf/soaa001",
    "type": "journal-article",
    "title": ["Article title"],              // array — take [0]
    "container-title": ["Social Forces"],    // journal name
    "short-container-title": ["Soc Forces"],
    "author": [
      {"given": "Jane Q.", "family": "Smith", "sequence": "first",
       "affiliation": [{"name": "UNC-Chapel Hill"}],
       "ORCID": "http://orcid.org/0000-0002-..."}
    ],
    "issued": {"date-parts": [[2020, 5, 1]]}, // [[year, month, day]]; may be [[year]]
    "volume": "99", "issue": "2",
    "page": "1-30",
    "ISSN": ["0037-7732"],
    "publisher": "Oxford University Press",
    "abstract": "<jats:p>...</jats:p>",       // JATS XML — strip tags
    "is-referenced-by-count": 42,             // citations (Crossref's count)
    "reference": [ /* cited works, if deposited */ ],
    "funder": [{"name": "NSF", "award": ["SES-1234567"]}],
    "license": [{"URL": "...", "content-version": "vor"}],
    "URL": "https://doi.org/10.1093/sf/soaa001"
  }
}
```

### Search works

```
GET /works?query=...                     # general relevance search
GET /works?query.bibliographic=...       # a full citation string (great for
                                         #   resolving a messy reference to a DOI)
GET /works?query.title=...&query.author=...
```

Useful parameters:
- `filter` — comma-separated, e.g.
  `filter=from-pub-date:2015-01-01,until-pub-date:2020-12-31,type:journal-article`
- `rows` — up to 1000 per page.
- `select` — return only chosen fields, e.g.
  `select=DOI,title,author,container-title,issued` (faster, smaller payloads).
- `sort` + `order` — e.g. `sort=relevance` or `sort=published&order=desc`.
- Deep paging: use `cursor=*` then follow `message.next-cursor` (do NOT use
  `offset` beyond 10k rows).

### Journals

```
GET /journals?query=social+forces        # find a journal + its ISSNs
GET /journals/{issn}/works               # works in a journal
```

### Funders / members

```
GET /funders?query=national+science+foundation
GET /works?filter=funder:{funder-id}
```

## Reliability notes

- Rate limits are dynamic; respect `X-Rate-Limit-Limit` / `X-Rate-Limit-Interval`
  response headers and back off on HTTP 429. The polite pool (`mailto`) is much
  more forgiving than anonymous.
- Not every field is present on every record — publishers deposit unevenly.
  Abstracts and reference lists are frequently missing. Never assume a field
  exists; guard for absence.
- `title` and `container-title` are **arrays**; take the first element.
- `abstract` is JATS XML — strip the `<jats:*>` tags before storing.

## Mapping Crossref → Zotero fields (for `scripts/zotero_db.py`)

| Crossref                          | Zotero item field        |
|-----------------------------------|--------------------------|
| `title[0]`                        | `title`                  |
| `author[].given` / `.family`      | `creators[].firstName` / `.lastName` (keep order) |
| `container-title[0]`              | `publicationTitle`       |
| `issued.date-parts[0]`            | `date` (join as `YYYY-MM-DD` or `YYYY`) |
| `volume` / `issue` / `page`       | `volume` / `issue` / `pages` |
| `DOI`                             | `DOI`                    |
| `ISSN[0]`                         | `ISSN`                   |
| `URL`                             | `url`                    |
| `abstract` (tags stripped)        | `abstractNote`           |
| `type: journal-article`           | `itemType: journalArticle` |
| `type: posted-content`            | `itemType: preprint`     |
| `type: book`/`book-chapter`       | `itemType: book`/`bookSection` |
| `type: proceedings-article`       | `itemType: conferencePaper` |

**Typical workflow:** discover candidates in OpenAlex → for each kept work, if
you have a DOI, fetch the Crossref record to get clean publisher metadata → map
to the Zotero JSON → add. If Crossref lacks the DOI or a field, fall back to the
OpenAlex values rather than leaving it blank. Never fabricate a value that
neither source returned.
