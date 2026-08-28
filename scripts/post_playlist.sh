#!/bin/bash
# POST a tracklist payload to the Soundiiz Playlist Import API.
# Usage: post_playlist.sh payload.json
# payload.json: {"title", "description"?, "sourceName"?, "destination"?, "tracklist":[{"title","artist"},...]}
set -euo pipefail
f="${1:?usage: post_playlist.sh payload.json}"

python3 - "$f" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
tl = d.get("tracklist", [])
assert d.get("title"), "payload missing 'title'"
assert 1 <= len(tl) <= 200, f"tracklist has {len(tl)} tracks, must be 1-200"
for i, t in enumerate(tl):
    assert t.get("title") and t.get("artist"), f"track #{i+1} missing title/artist: {t}"
PY

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
curl -s -X POST https://soundiiz.com/go/import-playlist \
  -H "Content-Type: application/json" --data-binary @"$f" -o "$tmp"

python3 - "$tmp" <<'PY'
import json, sys, datetime
try:
    r = json.load(open(sys.argv[1]))
except Exception:
    print("ERROR: non-JSON response from Soundiiz API:", file=sys.stderr)
    print(open(sys.argv[1]).read()[:500], file=sys.stderr)
    sys.exit(1)
if r.get("status") == "success":
    exp = datetime.datetime.fromtimestamp(r["expiresAt"]).strftime("%Y-%m-%d %H:%M")
    print(f"OK {r['nbTracks']} tracks")
    print(f"link: {r['shareUrl']}")
    print(f"expires: {exp}")
else:
    print(f"ERROR: {r.get('message', r)}", file=sys.stderr)
    sys.exit(1)
PY
