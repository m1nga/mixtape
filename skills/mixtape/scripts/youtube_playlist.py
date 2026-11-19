#!/usr/bin/env python3
"""Export exact YouTube URLs or verify a saved playlist against a pinned mixtape."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from canonicalize import check_recording_evidence, tracklist_fingerprint, youtube_recording_evidence


def expected_ids(manifest):
    tracks = manifest["tracklist"]
    evidence = manifest.get("_mixtape", {})
    catalog_verified = evidence.get("catalogVerified") is True
    if catalog_verified and tracklist_fingerprint(tracks) != evidence.get("tracklistSha256"):
        raise ValueError("Use the complete, unchanged catalog-verified tracklist.")
    if not catalog_verified and "youtubeRecordingSha256" not in evidence:
        raise ValueError("Pin recordings from the reviewed YouTube source first.")
    check_recording_evidence(evidence, youtube_recording_evidence(tracks))
    return [track["youtubeVideoId"] for track in tracks]


def read_playlist(playlist_id, token):
    if not re.fullmatch(r"PL[A-Za-z0-9_-]+", playlist_id):
        raise ValueError("Use the PL ID of the saved destination playlist.")
    if not token:
        raise ValueError("Destination read-back requires an authorized YOUTUBE_ACCESS_TOKEN.")
    params = {"part": "snippet,contentDetails", "playlistId": playlist_id, "maxResults": 50,
              "fields": "nextPageToken,pageInfo/totalResults,items(snippet/position,contentDetails/videoId)"}
    by_position = {}
    seen_tokens = set()
    total = None
    while True:
        url = "https://www.googleapis.com/youtube/v3/playlistItems?" + urlencode(params)
        request = Request(url, headers={"Authorization": f"Bearer {token}"})
        with urlopen(request, timeout=20) as response:
            page = json.load(response)
        page_total = page["pageInfo"]["totalResults"]
        if type(page_total) is not int or page_total < 0 or (total is not None and total != page_total):
            raise ValueError("Playlist count changed or was invalid during read-back. Read it again.")
        total = page_total
        for item in page["items"]:
            position = item["snippet"]["position"]
            if position in by_position:
                raise ValueError("Playlist positions changed during read-back. Read it again.")
            by_position[position] = item["contentDetails"]["videoId"]
        next_token = page.get("nextPageToken")
        if not next_token:
            break
        if next_token in seen_tokens:
            raise ValueError("YouTube repeated a page token. Read-back is incomplete.")
        seen_tokens.add(next_token)
        params["pageToken"] = next_token
    if sorted(by_position) != list(range(total)):
        raise ValueError("YouTube returned an incomplete list of positions. Read it again.")
    return [by_position[index] for index in range(len(by_position))]


def compare(playlist_id, expected, actual):
    return {
        "status": "verified" if actual == expected else "mismatch",
        "playlistId": playlist_id,
        "expectedCount": len(expected),
        "actualCount": len(actual),
        "expectedVideoIds": expected,
        "actualVideoIds": actual,
        "missingVideoIds": list((Counter(expected) - Counter(actual)).elements()),
        "unexpectedVideoIds": list((Counter(actual) - Counter(expected)).elements()),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write-urls", type=Path, help="write one watch URL per recording")
    action.add_argument("--playlist-id", help="read a saved YouTube PL playlist")
    action.add_argument("--pin-recordings", type=Path, help="capture ordered IDs and durations from the reviewed source")
    parser.add_argument("--duration-range", nargs=2, type=int, metavar=("MIN_MINUTES", "MAX_MINUTES"),
                        help="require a complete YouTube duration total within these inclusive minute bounds")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        evidence = manifest.setdefault("_mixtape", {})
        current = youtube_recording_evidence(manifest["tracklist"])
        check_recording_evidence(evidence, current)
        total = current["youtubeTotalDurationSeconds"]
        if args.duration_range:
            low, high = args.duration_range
            if low < 0 or high < low:
                raise ValueError("Use a nonnegative minimum and maximum in minutes.")
            if total is None:
                raise ValueError("The duration range requires an exact duration for every YouTube video.")
            if not low * 60 <= total <= high * 60:
                raise ValueError(f"YouTube recordings total {total} seconds, outside {low}–{high} minutes.")
        if args.pin_recordings:
            evidence.update(current)
        ids = expected_ids(manifest)
        if args.pin_recordings:
            with args.pin_recordings.open("x", encoding="utf-8") as output:
                json.dump(manifest, output, ensure_ascii=False, indent=2)
                output.write("\n")
            print(json.dumps({"status": "pinned", "tracks": len(ids), **current}))
            return 0
        if args.write_urls:
            urls = [f"https://www.youtube.com/watch?v={video_id}" for video_id in ids]
            with args.write_urls.open("x", encoding="utf-8") as output:
                output.write("\n".join(urls) + "\n")
            print(json.dumps({"status": "prepared", "tracks": len(ids), "file": str(args.write_urls),
                              "recordingFingerprintPresent": "youtubeRecordingSha256" in evidence,
                              "youtubeTotalDurationSeconds": total}))
            return 0
        if "youtubeRecordingSha256" not in evidence:
            raise ValueError("Legacy catalog fingerprint covers titles and artists only. Pin the original reviewed YouTube source before destination verification.")
        actual = read_playlist(args.playlist_id, os.environ.get("YOUTUBE_ACCESS_TOKEN"))
        receipt = {**compare(args.playlist_id, ids, actual), **current}
    except (OSError, URLError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"status": "blocked", "reason": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
