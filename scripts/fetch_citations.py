#!/usr/bin/env python3
"""
fetch_citations.py — refresh citation counts for publications.bib
and emit metrics.tex with \\cite<bibkey>{N} macros.

Usage:
    python scripts/fetch_citations.py \\
        --bib publications.bib \\
        --cache .cache/citations.json \\
        --out metrics.tex \\
        --ttl-days 7

Sources: Semantic Scholar primary (batch endpoint), OpenAlex fallback
on misses for entries with a DOI. Caches to .cache/citations.json with
a 7-day TTL so a fresh git clone can build the CV without network.
"""

from __future__ import annotations
import argparse, json, os, re, sys, time, datetime as dt
from pathlib import Path
from typing import Optional
import urllib.request, urllib.error

import bibtexparser  # pip install bibtexparser==1.4.*

S2_BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch"
OA_DOI   = "https://api.openalex.org/works/doi:{doi}"
USER_AGENT = "loevlie-cv-citation-fetcher/1.0 (mailto:dennis.loevlie@tufts.edu)"

S2_KEY = os.getenv("S2_API_KEY")
OA_KEY = os.getenv("OPENALEX_API_KEY")


def http_json(url, *, method="GET", body=None, headers=None, max_retries=5):
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})}
    data = json.dumps(body).encode() if body else None
    if data:
        headers["Content-Type"] = "application/json"
    for attempt in range(max_retries):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504):
                wait = (2 ** attempt) + 0.25 * attempt
                print(f"  retry {attempt+1}/{max_retries} after {wait}s ({e.code})", file=sys.stderr)
                time.sleep(wait)
                continue
            if e.code == 404:
                return None
            raise
        except urllib.error.URLError:
            time.sleep(2 ** attempt)
            continue
    return None


def normalize_id(entry):
    if doi := entry.get("doi"):
        return doi.strip().lower()
    if entry.get("archiveprefix", "").lower().startswith("arxiv") and entry.get("eprint"):
        return f"ARXIV:{entry['eprint'].strip()}"
    if m := re.search(r"arxiv\.org/abs/([\w./-]+)", (entry.get("url") or "") + (entry.get("eprint") or ""), re.I):
        return f"ARXIV:{m.group(1)}"
    return None


def fetch_s2_batch(ids):
    out = {pid: None for pid in ids}
    if not ids:
        return out
    headers = {"x-api-key": S2_KEY} if S2_KEY else {}
    url = f"{S2_BATCH}?fields=citationCount,externalIds,title"
    data = http_json(url, method="POST", body={"ids": ids}, headers=headers)
    if not data:
        return out
    for pid, rec in zip(ids, data):
        if rec and "citationCount" in rec and rec["citationCount"] is not None:
            out[pid] = int(rec["citationCount"])
    return out


def fetch_openalex_doi(doi):
    headers = {"Authorization": f"Bearer {OA_KEY}"} if OA_KEY else {}
    rec = http_json(OA_DOI.format(doi=doi), headers=headers)
    return int(rec["cited_by_count"]) if rec and "cited_by_count" in rec else None


def h_index(counts):
    h = 0
    for i, c in enumerate(sorted(counts, reverse=True), start=1):
        if c >= i:
            h = i
        else:
            break
    return h


def latex_escape_key(k):
    """\\newcommand names: only letters, no digits/underscores/colons."""
    return re.sub(r"[^A-Za-z]", "", k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib", required=True, type=Path)
    ap.add_argument("--cache", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--ttl-days", type=int, default=7)
    args = ap.parse_args()

    args.cache.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(args.cache.read_text()) if args.cache.exists() else {}
    now = dt.datetime.utcnow()

    with args.bib.open() as f:
        bib = bibtexparser.load(f)

    # Manual Google Scholar overrides — if a bib entry has a `scholar = {N}`
    # field, it takes precedence over the API-fetched count. Scholar usually
    # reports higher counts than Semantic Scholar (~30-50% for CS papers)
    # and there's no public Scholar API, so manual override is the cleanest
    # way to surface the numbers a user actually sees on their profile.
    for e in bib.entries:
        if "scholar" in e:
            try:
                cache[e["ID"]] = {
                    "paper_id": "scholar-manual",
                    "count": int(e["scholar"]),
                    "fetched": now.isoformat(timespec="seconds"),
                }
            except ValueError:
                print(f"  warn: bad scholar={e['scholar']!r} on {e['ID']}", file=sys.stderr)

    needs_refresh = {}
    for e in bib.entries:
        if "scholar" in e:
            continue                 # manual override wins; skip API lookup
        pid = normalize_id(e)
        if not pid:
            continue
        rec = cache.get(e["ID"])
        stale = (
            not rec
            or rec.get("paper_id") != pid
            or (now - dt.datetime.fromisoformat(rec["fetched"])).days >= args.ttl_days
        )
        if stale:
            needs_refresh[e["ID"]] = pid

    print(f"{len(needs_refresh)} of {len(bib.entries)} entries need API refresh "
          f"(plus {sum(1 for e in bib.entries if 'scholar' in e)} Scholar overrides)",
          file=sys.stderr)

    s2_results = {}
    pids = list(needs_refresh.values())
    for i in range(0, len(pids), 500):
        chunk = pids[i:i+500]
        s2_results.update(fetch_s2_batch(chunk))
        time.sleep(1.0 if not S2_KEY else 0.2)

    for bk, pid in needs_refresh.items():
        n = s2_results.get(pid)
        if n is None and not pid.startswith("ARXIV:"):
            n = fetch_openalex_doi(pid)
        if n is not None:
            cache[bk] = {"paper_id": pid, "count": n,
                         "fetched": now.isoformat(timespec="seconds")}

    args.cache.write_text(json.dumps(cache, indent=2, sort_keys=True))

    counts = [v["count"] for v in cache.values() if isinstance(v.get("count"), int)]
    total = sum(counts)
    h = h_index(counts)

    lines = [
        "% AUTO-GENERATED by scripts/fetch_citations.py — DO NOT EDIT",
        f"% Last refresh: {now.strftime('%Y-%m-%d')}",
        f"\\newcommand{{\\citationsTotal}}{{{total}}}",
        f"\\newcommand{{\\citationsHIndex}}{{{h}}}",
        f"\\newcommand{{\\citationsAsOf}}{{{now.strftime('%b %Y')}}}",
        "% Per-paper macros: \\cite<bibkey> -> N",
    ]
    for bk, rec in sorted(cache.items()):
        if isinstance(rec.get("count"), int):
            lines.append(f"\\newcommand{{\\cite{latex_escape_key(bk)}}}{{{rec['count']}}}")
    args.out.write_text("\n".join(lines) + "\n")
    print(f"wrote {args.out} (total={total}, h={h})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
