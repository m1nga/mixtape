---
name: mixtape
description: Make the user an authored playlist and deliver a verified one-click Soundiiz import link for Apple Music, YouTube Music, Spotify, Deezer, or Tidal without platform API keys. Supports quick orders from a scene or mood, expansion from seed songs, and taste-profile curation from playlists the user shares. Use for "make me a playlist," "songs for late-night coding," 给我来个歌单, 根据这几首帮我扩展, 找类似的歌, 分析我的听歌口味, or any request for songs to listen to. Not for audio narration, transferring an existing playlist unchanged, or controlling playback.
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
files on first use):

| File | Holds | Touch when |
|---|---|---|
| `taste.md` | 平台默认 · 硬性偏好(语言/年代/风格) · 细读发现(制作/人声/能量) · 挚爱曲目与艺人 · 雷区 | Read before EVERY generation; update after profile analysis or feedback |
| `history.md` | One section per mixtape: date, title, mode, platform, tracklist, feedback | Append after every delivery |
| `misses.md` | Tracks that failed to match on a platform: `- 歌名 — 艺人 (平台, 日期)` | Read before generating (avoid repeats); append when user reports 缺歌 |

The profile is what makes the agent smarter over time. A one-line update after each
session beats a perfect schema. Two rules keep it honest: what the user says *now*
always beats what the files remember (update the file, don't argue), and a single
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
change the songs; otherwise decide and go — the import page is itself a preview, so
a wrong guess costs one click, not a conversation.

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
- ≤200 tracks per link (API cap). More → split into volumes (Vol.1, Vol.2), one
  link each, mind the 10 requests/min rate limit.

## Delivery

1. Show the numbered tracklist in chat (with 已听/新 tags in profile mode, and the
   one-line group inferences in seed mode).
2. Write the payload to a JSON file in the session scratchpad (or any temp dir):
   ```json
   {"title": "...", "description": "...", "sourceName": "Mixtape",
    "destination": "youtube",
    "tracklist": [{"title": "...", "artists": ["...", "..."]}]}
   ```
3. **Canonicalize before posting**: `python3 <skill-dir>/scripts/canonicalize.py
   payload.json --country <storefront>`. The script verifies title **and artist**,
   rejects wrong artists and unwanted versions, rewrites confirmed tracks to the
   Apple catalog's displayed metadata, and writes an evidence report. It exits
   nonzero when any track is unconfirmed; replace those tracks and rerun. Use the
   user's storefront country (record it in `taste.md`, e.g. GB).
   If free-text search misses a song but an official Apple Music song page proves
   it exists, add its numeric URL ID as `"appleMusicId": 1702056850` on that track
   and rerun. The script looks that ID up in the target storefront and still
   verifies its title+artist; this is evidence, never a bypass.
4. POST only the signed canonical file: `bash
   <skill-dir>/scripts/post_playlist.sh payload.canonical.json`. The poster refuses
   unverified or post-verification edits, strips internal evidence metadata, and
   sends Soundiiz its documented `artists` field. **Never send `artist` (singular):
   Soundiiz accepts the request but ignores that field, leaving it to match by title
   alone.** The script prints the import link and expiry on success.
5. Hand over the link with: 有效期 24 小时;打开 → 确认目标平台 → 导入。That
   confirmation click doubles as the user's preview/veto step — do not try to
   automate it away.

**Destination preselect** (`destination` field): verified corenames `spotify`,
`ytmusic` (YouTube Music), `youtube` (plain YouTube video playlist — prefer
`ytmusic` when the user says "YouTube" but means music), `deezer`, `tidal`.
**Apple Music has no preselect corename** — omit the
field and tell the user to pick Apple Music on the import page (one tap; their
Soundiiz account holds the platform authorization). Remember the user's platform in
`taste.md` and stop asking.

## Iteration: one complete playlist per version

A revision is never a patch and never a restart. Start from the previous version's
tracklist in `history.md`, keep every track the user hasn't vetoed, apply the
changes (swaps, new ratios, extensions), and ship **one complete replacement
playlist** with a versioned title (v2, v3…) — telling the user to delete the
previously imported one. The user's confirmed-loved tracks are the asset being
built; a from-scratch regeneration throws that away, and a patch link leaves them
managing fragments. Log each version's lineage in `history.md` (迭代自 vN).

## After the import (lightweight, never nagging)

One line when delivering: 导入后如果有没匹配上或踩雷的歌，说一声。When they report:

- **缺歌** → append to `misses.md`; the replacements go into the next complete
  version (a small top-up link only if the user says they prefer patching).
- **踩雷** → record to `taste.md` 雷区 with the *reason* if given (太吵? 年代不对?).
- Log the mixtape to `history.md` either way.

## When things break

- Tracks still 未找到 on import despite canonical names → Soundiiz's batch matcher
  itself flakes (even "One More Time — Daft Punk" can fail once). Re-issue just the
  missing tracks as a smaller top-up link rather than telling the user to fix them
  by hand.
- `Too many requests` → wait 60s, retry once.
- API error or format change → don't strand the user: deliver the tracklist as
  plain text plus manual path (soundiiz.com → Import playlist → paste text), and
  note the API issue so the skill can be updated.
- Free Soundiiz converts one playlist (≤200 tracks) per transfer — normal personal
  use never hits this; only mention limits if the user does.
