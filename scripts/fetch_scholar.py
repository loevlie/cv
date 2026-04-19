#!/usr/bin/env python3
"""
fetch_scholar.py — Google Scholar citation refresh via author-profile lookup.

Usage:
    python scripts/fetch_scholar.py \
        --bib publications.bib \
        --author-id oGkEIYkAAAAJ \
        --out metrics_scholar.tex

Strategy (one HTTP round-trip per run, max):
  1. Fetch the author profile (via `scholarly`) — yields ALL publications
     with their citedby_url + num_citations in a single fill().
  2. Fuzzy-match each Scholar publication to a `.bib` entry by title.
  3. Write metrics_scholar.tex with \citationsTotal / \citationsHIndex /
     \citeXXX{N} macros.

Anti-block notes:
  - Scholar reCAPTCHA-walls fresh IPs after ~5-50 requests. Profile-level
    queries are MUCH less aggressive than per-paper queries (N=1 vs N=5
    requests). With a 7-day TTL cache the effective rate is well under
    1 request/week from any given IP.
  - On block (CAPTCHA / 429), the script exits non-zero WITHOUT touching
    the existing metrics_scholar.tex — the previous-week values stay live.
  - Manual override: any `.bib` entry with `scholar = {N}` is honored
    verbatim, bypassing Scholar entirely. Use this for entries Scholar
    can't disambiguate or when scraping fails.

Recommended: run weekly via cron, accept that it will sometimes fail
gracefully, and refresh manually via the .bib `scholar = {N}` field
when you notice numbers are stale.
"""

from __future__ import annotations
import argparse, json, os, re, sys, datetime as dt
from difflib import SequenceMatcher
from pathlib import Path

import bibtexparser  # pip install bibtexparser==1.4.*
from scholarly import scholarly, ProxyGenerator  # pip install scholarly


def normalize(s: str) -> str:
    """Lowercase + strip non-alnum for fuzzy title matching."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def best_match(title: str, candidates: list[dict], threshold: float = 0.85) -> dict | None:
    """Return the candidate whose 'title' field is most similar to `title`,
    or None if best similarity < threshold."""
    target = normalize(title)
    best, best_score = None, 0.0
    for cand in candidates:
        cand_title = normalize(cand.get("bib", {}).get("title", ""))
        if not cand_title:
            continue
        score = SequenceMatcher(None, target, cand_title).ratio()
        if score > best_score:
            best_score, best = score, cand
    return best if best_score >= threshold else None


def h_index(counts: list[int]) -> int:
    h = 0
    for i, c in enumerate(sorted(counts, reverse=True), start=1):
        if c >= i:
            h = i
        else:
            break
    return h


def latex_escape_key(k: str) -> str:
    return re.sub(r"[^A-Za-z]", "", k)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib", required=True, type=Path)
    ap.add_argument("--author-id", required=True,
                    help="Google Scholar user ID, e.g. oGkEIYkAAAAJ")
    ap.add_argument("--out", required=True, type=Path,
                    help="LaTeX file to emit with \\citationsTotal etc.")
    ap.add_argument("--proxy", action="store_true",
                    help="Use scholarly.ProxyGenerator (slower, more reliable)")
    args = ap.parse_args()

    if args.proxy:
        pg = ProxyGenerator()
        if not pg.FreeProxies():
            print("warn: ProxyGenerator setup failed; continuing without", file=sys.stderr)
        else:
            scholarly.use_proxy(pg)

    # 1. Fetch author profile + fill all publications in one go
    try:
        print(f"Fetching Scholar profile {args.author_id}...", file=sys.stderr)
        author = scholarly.search_author_id(args.author_id)
        scholarly.fill(author, sections=["basics", "publications"])
    except Exception as e:
        print(f"ERROR: Scholar fetch failed ({type(e).__name__}: {e}). "
              f"Existing {args.out} (if any) is unchanged.", file=sys.stderr)
        return 1

    pubs = author.get("publications", [])
    # Each pub has 'bib' with 'title' and 'num_citations' on the publication
    # object itself (post-fill on the author it's already populated).
    print(f"  {len(pubs)} publications on Scholar profile", file=sys.stderr)

    # 2. Match against .bib entries
    with args.bib.open() as f:
        bib = bibtexparser.load(f)

    counts: dict[str, int] = {}
    matched: list[tuple[str, str, int]] = []
    unmatched_bib: list[str] = []

    for entry in bib.entries:
        if "scholar" in entry:
            try:
                counts[entry["ID"]] = int(entry["scholar"])
                matched.append((entry["ID"], "[manual scholar override]",
                                int(entry["scholar"])))
                continue
            except ValueError:
                pass

        title = entry.get("title", "").strip("{}")
        m = best_match(title, pubs)
        if m is None:
            unmatched_bib.append(entry["ID"])
            continue
        n = int(m.get("num_citations", 0))
        counts[entry["ID"]] = n
        matched.append((entry["ID"], m["bib"]["title"][:60], n))

    # 3. Emit metrics_scholar.tex
    now = dt.datetime.now(dt.timezone.utc)
    total = sum(counts.values())
    h = h_index(list(counts.values()))

    lines = [
        "% AUTO-GENERATED by scripts/fetch_scholar.py — DO NOT EDIT",
        f"% Last refresh: {now.strftime('%Y-%m-%d')} (Google Scholar)",
        f"\\newcommand{{\\citationsTotalScholar}}{{{total}}}",
        f"\\newcommand{{\\citationsHIndexScholar}}{{{h}}}",
        f"\\newcommand{{\\citationsAsOfScholar}}{{{now.strftime('%b %Y')}}}",
        "% Per-paper macros: \\citeS<bibkey> -> N",
    ]
    for bk in sorted(counts):
        lines.append(f"\\newcommand{{\\citeS{latex_escape_key(bk)}}}{{{counts[bk]}}}")
    args.out.write_text("\n".join(lines) + "\n")

    # 4. Report
    print(f"\nMatched ({len(matched)}):", file=sys.stderr)
    for bk, title, n in matched:
        print(f"  {n:>4}  {bk:<28}  {title}", file=sys.stderr)
    if unmatched_bib:
        print(f"\nNo Scholar match for ({len(unmatched_bib)}):", file=sys.stderr)
        for bk in unmatched_bib:
            print(f"  - {bk}", file=sys.stderr)
        print("(Add `scholar = {N}` to the bib entry to override.)", file=sys.stderr)
    print(f"\nWrote {args.out} (total={total}, h={h})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
