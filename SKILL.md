---
name: mixtape
description: Make the user their OWN playlist — a mixtape they authored, not another stranger's list — and deliver it as a one-click Soundiiz import link into their streaming account (Apple Music, YouTube, Spotify, Deezer, Tidal; no platform API keys needed). Three modes — quick order (describe a scene/mood/genre → full playlist), seed expansion (user gives a few example songs, optionally grouped by sub-style → more that belong with each group), and taste-profile curation (analyze playlists the user shares, keep a persistent profile in ~/.mixtape/, blend songs they love with adjacent discoveries). Use whenever the user asks for a playlist or for songs to listen to — "make me a playlist", "playlist for late-night coding", 给我来个歌单 / 建个歌单 / 来点适合〇〇的歌 / 根据这几首帮我扩展 / 找类似的歌 / 分析我的听歌口味 — or shares seed songs wanting more like them, even without the word "playlist". NOT for turning documents or text into listenable audio programs, NOT for transferring existing playlists between platforms (plain soundiiz.com does that), NOT for playing or controlling music playback.
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
- **Canonical form matches best**: main title + primary artist (one artist name —
  multi-artist credits are the likeliest matching failures). Drop "feat.",
  "(Live)", "(Remix)" qualifiers unless the user wants that specific version —
  Soundiiz's matcher does better with clean names. For non-Latin catalogs, use the
  form streaming platforms dominantly list (Japanese/Chinese titles usually stay in
  the original script; when unsure, original script is the safer match).
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
    "destination": "youtube", "tracklist": [{"title": "...", "artist": "..."}]}
   ```
3. **Canonicalize before posting** — this step is what makes imports actually
   match: `python3 <skill-dir>/scripts/canonicalize.py payload.json --country <storefront>`.
   Soundiiz matches on near-exact title+artist text, and official credits are
   rarely what you'd guess ("Rumble" is credited "Skrillex, Fred again.. &
   Flowdan"; Peggy Gou's title is "(It Goes Like) Nanana"; Taiwanese bands may use
   English names on Western storefronts). The script rewrites every track to the
   Apple catalog's exact spelling (helps all destinations, since it also proves the
   song exists as written) and reports unconfirmed tracks — replace those before
   posting, they will not import. Use the user's storefront country (record it in
   `taste.md` next to the platform, e.g. GB).
4. POST the canonicalized file: `bash <skill-dir>/scripts/post_playlist.sh payload.canonical.json`
   — prints the import link and expiry on success.
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

## After the import (lightweight, never nagging)

One line when delivering: 导入后如果有没匹配上或踩雷的歌，说一声。When they report:

- **缺歌** → append to `misses.md`, offer replacements — a small top-up link with
  just the substitutes beats regenerating everything.
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
