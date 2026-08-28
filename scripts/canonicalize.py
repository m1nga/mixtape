#!/usr/bin/env python3
"""Canonicalize a Mixtape payload against the Apple Music catalog (iTunes Search API).

Soundiiz matches strictly on title+artist text, so a track fails to import when our
spelling differs from the catalog's official credit (e.g. "Rumble — Skrillex" vs the
official "Skrillex, Fred again.. & Flowdan"). This script looks every track up in
Apple's catalog (free API, no key) and rewrites the payload with the catalog's exact
trackName/artistName. Tracks not found in the catalog are kept but reported, so the
agent can propose replacements before posting.

Usage: canonicalize.py payload.json [--country gb] [--out payload.canonical.json]
"""
import difflib, json, re, sys, time, urllib.parse, urllib.request

BAD_QUALIFIERS = re.compile(
    r"\b(mixed|live|karaoke|tribute|cover|instrumental|sped up|slowed|8d|remix)\b", re.I)


def search(term, country, limit=10):
    url = ("https://itunes.apple.com/search?term=" + urllib.parse.quote(term)
           + f"&entity=song&country={country}&limit={limit}")
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.load(r)["results"]


def norm(s):
    return re.sub(r"[^\w一-鿿]+", "", s.lower())


def score(track, want_title, want_artist):
    title_sim = difflib.SequenceMatcher(
        None, norm(want_title), norm(track["trackName"])).ratio()
    artist_sim = difflib.SequenceMatcher(
        None, norm(want_artist), norm(track["artistName"])).ratio()
    artist_contains = norm(want_artist) in norm(track["artistName"]) or \
        norm(track["artistName"]) in norm(want_artist)
    penalty = 0.35 if BAD_QUALIFIERS.search(track["trackName"]) else 0.0
    length_penalty = min(len(track["trackName"]) / 400, 0.15)
    return title_sim * 2 + artist_sim + (0.5 if artist_contains else 0) - penalty - length_penalty


def canonicalize(title, artist, country):
    results = []
    for term in (f"{title} {artist}", title):
        try:
            results = search(term, country)
        except Exception as e:
            print(f"  ⚠️ API error for {title!r}: {e}", file=sys.stderr)
        if results:
            break
        time.sleep(0.6)
    if not results:
        return None
    best = max(results, key=lambda t: score(t, title, artist))
    if score(best, title, artist) < 1.0:  # nothing plausibly the same song
        return None
    return {"title": best["trackName"], "artist": best["artistName"]}


def main():
    args = sys.argv[1:]
    path = args[0]
    country = args[args.index("--country") + 1] if "--country" in args else "us"
    out = args[args.index("--out") + 1] if "--out" in args else \
        re.sub(r"\.json$", "", path) + ".canonical.json"
    payload = json.load(open(path))
    not_found, changed = [], 0
    for i, t in enumerate(payload.get("tracklist", [])):
        c = canonicalize(t["title"], t["artist"], country)
        if c is None:
            not_found.append(f'{t["title"]} — {t["artist"]}')
            print(f"❌ not confirmed in catalog: {t['title']} — {t['artist']}")
        else:
            if (c["title"], c["artist"]) != (t["title"], t["artist"]):
                changed += 1
                print(f"✏️  {t['title']} — {t['artist']}\n    → {c['title']} — {c['artist']}")
            else:
                print(f"✅ {t['title']} — {t['artist']}")
            payload["tracklist"][i] = c
        time.sleep(0.6)
    json.dump(payload, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"\n{changed} rewritten, {len(not_found)} unconfirmed → {out}")
    if not_found:
        print("Consider replacing the unconfirmed tracks before posting:")
        for x in not_found:
            print(f"  - {x}")


if __name__ == "__main__":
    main()
