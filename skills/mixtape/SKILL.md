---
name: mixtape
description: Build a playlist from a mood, seed songs, or listening history. Save and verify ordered playlists in an authorized YouTube or YouTube Music account, or prepare a catalog-checked Soundiiz import for other or undecided services. Use for new playlists, revisions, or missing tracks, including 给我来个歌单, 扩展这几首, and 分析我的听歌口味. Excludes playback control and unchanged cross-service transfers.
---

# Mixtape · 亲手做的歌单

Everyone's library is full of playlists made by strangers and algorithms. A mixtape
is different: it is *authored*. The user brings the taste; you are the hands that do
the hours of searching, matching, and arranging they never have time for. Everything
below serves that one feeling — "this playlist is MINE" — so never pad with generic
chart hits when the request implies specificity, and always be able to say why a
track earned its slot.

Reply in the user's language. Playlist titles should sound like something the user
would name, not like an algorithm ("周五晚·华语摇滚快车", not "Chinese Rock Mix #1").

## State: ~/.mixtape/

Persistent memory lives outside this package in `~/.mixtape/` (create it and the
files on first use when the host provides durable storage):

| File | Holds | Touch when |
|---|---|---|
| `taste.md` | 平台默认 · 硬性偏好(语言/年代/风格) · 细读发现(制作/人声/能量) · 挚爱曲目与艺人 · 雷区 | Read before EVERY generation; update after profile analysis or feedback |
| `history.md` | One section per mixtape: date, title, mode, platform, tracklist, feedback | Append after every delivery |
| `misses.md` | Tracks that failed to match on a platform: `- 歌名 — 艺人 (平台, 日期)` | Read before generating (avoid repeats); append when user reports 缺歌 |

The profile is what makes the agent smarter over time. A one-line update after each
session beats a perfect schema. In a temporary web workspace, only promise
cross-chat recovery if the host can reopen the same storage. Two rules keep it
honest: what the user says *now* always beats what the files remember, and a single
scene order is not taste evidence — a first-time "City Pop for cooking" records the
platform default, not "likes City Pop".

## Pick the mode

| Signal in the request | Mode |
|---|---|
| A scene/mood/genre described in words ("健身摇滚", "深夜写代码") | **快速点单** — generate directly |
| Example songs given, possibly grouped ("我喜欢的朋克是这几首、英伦是这几首") | **种子扩展** — anchor on the examples |
| User shares existing playlists, or asks 分析我的口味 / "what do I actually like" | **口味档案** — analyze first, then curate |

Modes stack: a quick order from a user with a taste profile on file should still be
filtered through that profile.

**快速点单.** Parse genre, scene, mood, era, language, count, platform. Default 25
tracks. Ask at most one clarifying question, and only if the answer would genuinely
change the result. Use the service the user named and honor requests for a preview.

**种子扩展.** The examples are evidence of what the user *actually* means by a genre
word. For each group, state in one line what you infer the seeds share (era?
production? vocal style? energy?) — this shows your reasoning and lets the user
correct it cheaply. Then generate neighbors per group, keeping the groups'
proportions. Include the seeds themselves unless asked for all-new songs; a
requested count is the total *including* seeds. Seed artists may recur, but keep
them under about a third of the list — expansion should widen the circle, not loop
it. Weave the groups into one arc rather than leaving them as contiguous blocks,
unless the user asks for separated chapters.

**口味档案.** Ingest whatever the user can give: pasted track lists, an exported
file, a public playlist URL (fetch it), or walk them through Soundiiz's export to
text. Look past the user's own label — they may say 抒情, but what the tracks
actually share might be "90s 港台 production + male falsetto + piano intros". Write
the findings to `taste.md`, then curate playlists that blend **已听过的挚爱 (~40%)**
with **没听过但相邻的发现 (~60%)** — ratio adjustable, and tag which is which when
presenting so the user sees both comfort and discovery.

## Generation rules

- **Real songs only.** Every track must be a real, released recording. The bar for
  "sure": you could name the album or era it came from. Below that bar, verify with
  a web search — an invented song silently becomes a wrong match on import, which
  is worse than one fewer track.
- **Canonical form matches best**: main title + the real artist credit. Keep
  collaborating artists as separate values in the `artists` array; drop "feat.",
  "(Live)", and "(Remix)" qualifiers unless the user wants that specific version.
  For non-Latin catalogs, use the form streaming platforms dominantly list
  (Japanese/Chinese titles usually stay in the original script).
- Check `misses.md`; don't re-recommend a track that already failed on the target
  platform.
- **Order is authorship.** Arrange an arc that fits the scene: workout ramps up,
  late-night descends, 通勤 stays level. A shuffled list is a search result, not a
  mixtape.

## Delivery

Use the requested service or the saved default. For YouTube and YouTube Music,
use the native workflow. Use Soundiiz for a requested import link, other supported
services, or a choice of services at import. For a tracklist preview, show the
tracks and wait for the user to request saving.

## YouTube saved playlists

1. **Pin the recordings.** Match title, artist and version on the requested
   service. Record the exact `youtubeVideoId` and verified `durationSeconds`
   for each position. For a duration request, sum the selected recordings,
   including each repeat, and adjust the selection before presenting it.
   For example, use a 58–62 minute window for an approximately one-hour mix.
   Seal the ordered recording evidence before saving:
   `python3 <skill-dir>/scripts/youtube_playlist.py reviewed.json --pin-recordings pinned.json --duration-range 58 62`.
   The time window is optional. If an exact duration is missing, leave the
   total unverified. Retain the pinned IDs for unchanged tracks in revisions.
   Apple catalog matching and YouTube recording evidence use separate fingerprints.
2. **Save into the account.** Use the authorized signed-in target. Find the
   existing playlist in the account library and reuse its exact `PL...` ID.
   For a new mix, create one playlist with the agreed title and default to private.
   Record its ID as soon as it exists. On YouTube, use **Add videos** with each exact
   watch URL, or **Save** on the video page. On YouTube Music, use **Add to
   playlist** on the matched recording. Preserve existing privacy, add the
   missing entries and put them in order. On resume or an uncertain write,
   read the saved state before retrying. If an existing target is ambiguous,
   ask for its link.
3. **Reopen and verify.** From the account library, reopen the saved playlist
   on the requested service. Read every saved item and compare the ordered
   video IDs, including duplicates, with the intended list. Confirm the visible
   total and playlist ID. Fix discrepancies in the same playlist and reread.
   YouTube Music can show fewer items than YouTube, so verify in Music when
   that is the requested destination.

Deliver the saved playlist URL, verified count, and the total from the exact
recordings when known. Mark the history entry verified only after the requested
library passes read-back. The helper's `--playlist-id` reads YouTube Data API IDs;
for YouTube Music, also reopen the playlist in Music. A temporary queue, import
count, or save notification alone leaves verification pending. If account access or complete read-back is blocked, state
the blocker, keep the ordered watch links, and request only what is needed to resume.

## Soundiiz import links

1. Show the ordered tracks. Write a scratch JSON payload with `title`,
   `description`, `sourceName: "Mixtape"`, and `tracklist` entries containing
   `title` and `artists` (array). Set `destination` to the chosen service. Omit it when the
   user wants to choose during import or no service is known. Values include `applemusicapp`, `spotify`, `youtube`, `ytmusic`,
   `deezer`, and `tidal`.
2. Run `python3 <skill-dir>/scripts/canonicalize.py payload.json --country <storefront>`.
   Verify title and artist in the user's Apple Music storefront. For a missed
   search with an official song page, set the track's numeric `appleMusicId`
   and rerun. Resolve any unconfirmed recording before posting.
3. Run `bash <skill-dir>/scripts/post_playlist.sh payload.canonical.json`.
   It checks the catalog fingerprint, submits the documented `artists` field,
   and returns an import link valid for 24 hours. Split lists over 200 tracks into
   volumes and stay within 10 requests per minute.
4. Give the verified catalog count and link expiry. The user confirms the
   destination and transfer in Soundiiz. Verify the imported count and
   recordings when a destination receipt is available. For YouTube imports,
   use the account read-back above. Keep the destination status pending until
   the saved result can be checked.

## Iteration: one living playlist with a stable identity

Build revisions from the full tracklist in `history.md`. Keep retained tracks
and apply the requested swaps, ratio changes or extensions. Prefer in-place
edits, especially for YouTube.

Keep the accepted user-facing title stable across revisions. **Never add v2/v3/v4,
“修复版”, or similar release bookkeeping to the title in the streaming library
unless the user explicitly asks for it.** Record revision numbers and lineage only
inside `history.md`. If direct in-place editing is unavailable and Soundiiz must
create a replacement, that replacement is temporary until the library is
reconciled: the user should end with exactly one current playlist under the stable
title, not a stack of versions and not a patch playlist.

After the replacement import succeeds:

1. Read the platform library and resolve the retained playlist plus every
   Mixtape-managed predecessor by exact platform ID, current name, and track count.
2. Preserve unrelated playlists even when their names look similar. Never delete
   by a fuzzy title search or by an unresolved variable/glob.
3. Check the retained playlist has the expected complete track count, rename it to
   the stable title, and delete only the explicitly resolved predecessor IDs.
4. Read the library again. Completion requires one playlist with the stable title,
   the expected track count, and no predecessor IDs. Log this receipt in
   `history.md`; do not claim success from the mutation call alone.

On macOS Apple Music, use the guarded helper rather than hand-written destructive
AppleScript:

```bash
python3 <skill-dir>/scripts/reconcile_apple_music.py inventory
python3 <skill-dir>/scripts/reconcile_apple_music.py reconcile manifest.json
python3 <skill-dir>/scripts/reconcile_apple_music.py reconcile manifest.json --apply
```

Manifest shape:

```json
{"stableTitle":"跑步",
 "keep":{"id":"6073","expectedName":"梦想感起跑 v4","expectedTrackCount":33},
 "delete":[{"id":"6059","expectedName":"梦想感起跑 v3","expectedTrackCount":8}],
 "protect":[{"id":"5334","expectedName":"I wonder if you know","expectedTrackCount":1}]}
```

It names the stable title, retained ID/name/count, and exact predecessor
IDs/names/counts. Add must-not-change playlists to optional `protect`; they are
checked before the plan and reported unchanged in the final receipt.
Reconciliation is dry-run by default; `--apply` refuses stale names, wrong counts,
unmanaged title collisions, or an ID listed in conflicting roles, then prints a
verified read-back receipt. Use another authorized platform API/connector for
other services with the same preflight → mutate → read-back contract. If no
authorized write surface exists, say so plainly and leave the reconciled state
unclaimed rather than telling the user a duplicate is “the new version.”

## Feedback

When the user gives feedback:

- **缺歌** → append to `misses.md`; repair the matcher or replace the failures in
  the next complete iteration. A top-up link is allowed only when the user
  explicitly asks to manage a patch separately.
- **踩雷** → record to `taste.md` 雷区 with the *reason* if given (太吵? 年代不对?).

## Soundiiz recovery

- Tracks still 未找到 on import despite canonical names → treat it as a failed
  delivery, not user cleanup. Re-check the target storefront, replace or pin the
  unresolved catalog IDs, regenerate the **complete** fingerprinted playlist, then
  reconcile it back to the stable platform identity. Do not default to a top-up
  fragment.
- `Too many requests` → wait 60s, retry once.
- API error or format change → deliver the ordered tracklist as one
  `Artist - Title` entry per line. Give the [Soundiiz plain-text import steps](https://support.soundiiz.com/hc/en-us/articles/37958924057234-How-to-Import-a-Playlist-from-a-URL-CSV-File-or-Plain-Text)
  and keep the import link and destination statuses separate. The manual route
  still needs the user's confirmation and a destination match check.
