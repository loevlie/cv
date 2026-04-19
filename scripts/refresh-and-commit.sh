#!/usr/bin/env bash
# Weekly local refresh: pulls fresh citation counts from Semantic Scholar
# AND Google Scholar, regenerates metrics files, and commits + pushes if
# anything changed. Designed to be run by launchd (or cron) once a week.
#
# Idempotent: no commits/pushes if nothing changed. Logs to stderr.
# Exit codes: 0 = ran, may or may not have committed; non-zero only on
# unrecoverable error (network, git auth).

set -u
cd "$(dirname "$0")/.."

REPO_ROOT="$PWD"
LOG_PREFIX="[$(date -u +%Y-%m-%dT%H:%M:%SZ)]"
echo "$LOG_PREFIX refresh-and-commit starting in $REPO_ROOT" >&2

# --- 0. Ensure tools available -------------------------------------------
PYTHON="${PYTHON:-/Users/dennisloevlie/miniconda3/bin/python3}"
GIT="${GIT:-/usr/bin/git}"
command -v "$GIT" >/dev/null || { echo "$LOG_PREFIX git not found" >&2; exit 2; }
"$PYTHON" -c "import bibtexparser, scholarly" 2>/dev/null \
  || { echo "$LOG_PREFIX missing deps; pip install bibtexparser scholarly" >&2; exit 2; }

# --- 1. Pull latest so we don't overwrite an upstream commit -------------
"$GIT" pull --rebase --autostash 2>&1 | sed "s|^|$LOG_PREFIX git pull: |" >&2

# --- 2. Refresh Semantic Scholar (fast, reliable) ------------------------
mkdir -p .cache
"$PYTHON" scripts/fetch_citations.py \
  --bib publications.bib \
  --cache .cache/citations.json \
  --out metrics.tex \
  --ttl-days 7 \
  2>&1 | sed "s|^|$LOG_PREFIX s2: |" >&2 || \
  echo "$LOG_PREFIX s2 refresh failed (continuing)" >&2

# --- 3. Refresh Google Scholar (fragile, fall back gracefully) ----------
"$PYTHON" scripts/fetch_scholar.py \
  --bib publications.bib \
  --author-id oGkEIYkAAAAJ \
  --out metrics_scholar.tex \
  2>&1 | sed "s|^|$LOG_PREFIX scholar: |" >&2 || \
  echo "$LOG_PREFIX scholar refresh failed (existing metrics_scholar.tex unchanged)" >&2

# --- 4. Commit + push if anything changed --------------------------------
"$GIT" add metrics.tex metrics_scholar.tex .cache/citations.json 2>/dev/null
if "$GIT" diff --cached --quiet; then
  echo "$LOG_PREFIX no changes to commit" >&2
else
  "$GIT" -c user.name="cv-bot (local)" \
         -c user.email="dennis.loevlie@tufts.edu" \
         commit -m "chore: refresh citation metrics ($(date -u +%Y-%m-%d))" \
         2>&1 | sed "s|^|$LOG_PREFIX git commit: |" >&2
  "$GIT" push 2>&1 | sed "s|^|$LOG_PREFIX git push: |" >&2 || \
    { echo "$LOG_PREFIX push failed" >&2; exit 3; }
fi

echo "$LOG_PREFIX done" >&2
