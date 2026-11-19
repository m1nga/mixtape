# Mixtape Playlist Builder — Make a Mood Playlist and Check Every Track

Mixtape is an agent skill for **OpenAI Codex** and **Claude Code**. Describe a
mood, share seed songs, or give it a playlist you love. It picks real recordings
and puts them in an order that fits.

- **YouTube and YouTube Music** — With authorized access to your signed-in account,
  Mixtape saves the exact recordings, reopens the account playlist, and checks
  every video ID and its position. When duration is requested, it checks the
  selected recordings against the time window before saving.
- **Apple Music, Spotify and other import destinations** — Mixtape checks the
  Apple Music catalog and prepares a [Soundiiz](https://soundiiz.com) link. You
  review the tracklist and confirm the transfer in Soundiiz.

Want the studio recording rather than a live version or cover? State that in the
request. For the import route, Mixtape checks the recordings in the named Apple storefront,
then keeps the destination import pending until it has a receipt. Soundiiz
[documents why transfers can still choose another version](https://support.soundiiz.com/hc/en-us/articles/32567703886098-Wrong-Track-Matches-Causes-How-to-Fix-Them);
check the destination count and recordings after import.

> "Use $mixtape to make a five-song late-night electronic playlist. Start with
> 'A Walk' by Tycho, build gently, and finish somewhere quiet. Check the US Apple
> Music catalog and give me one link where I can choose Apple Music or Spotify."

One sample result, **Low Light, Steady Hands**:

1. Tycho — A Walk
2. Yppah — Never Mess With Sunday
3. Bonobo — Kerala
4. Four Tet — Two Thousand and Seventeen
5. Brian Eno — An Ending (Ascent)

| Check | Sample status |
|---|---|
| Apple catalog | 5 of 5 recordings confirmed in the US storefront |
| Soundiiz import preview | Soundiiz accepted all 5 tracks and opened the playlist preview without a preset destination |
| Destination library | Awaiting user confirmation and a transfer result |

Each Soundiiz import link expires after 24 hours. To try the same example, use
[the sample tracklist](skills/mixtape/examples/low-light.json) from a fresh
checkout of this repository. Run these commands from its root to check the catalog
and create your own preview link:

```bash
mixtape_preview=$(mktemp -d)
python3 skills/mixtape/scripts/canonicalize.py skills/mixtape/examples/low-light.json \
  --country us --out "$mixtape_preview/playlist.json" --report "$mixtape_preview/catalog.json"
bash skills/mixtape/scripts/post_playlist.sh "$mixtape_preview/playlist.json"
```

After import, compare the count and recording versions in your destination.
If the link fails, Mixtape can give you a paste-ready `Artist - Title` list for
[Soundiiz's plain-text import](https://support.soundiiz.com/hc/en-us/articles/37958924057234-How-to-Import-a-Playlist-from-a-URL-CSV-File-or-Plain-Text).

## What it does

Mixtape turns a mood, a few seed songs, or the playlists you already love into a
sequenced playlist you authored. For the Soundiiz route, it checks
every title **and artist** against the selected Apple Music storefront, rejects
wrong covers/remixes/DJ-mix versions, and produces a catalog evidence report. A
fingerprint check then prevents unverified or subsequently edited tracklists from
being posted. Iterations keep one stable library identity: revision labels stay in
the private history, while the streaming playlist keeps its human title and
in-place edits preserve the original playlist ID where supported.

That matching layer matters. A beautiful 33-track recommendation is still a broken
product when only eight songs arrive in the user's library.

## When it fires

- Describe a scene: “late-night coding, warm electronic, 90 minutes.”
- Give seed tracks: “these are the three kinds of rock I mean—expand them.”
- Share existing playlists: “work out what I actually like, then mix familiar songs
  with discoveries.”
- Report a failed import: Mixtape records misses, repairs the matcher, and updates
  one complete playlist instead of making you manage fragments or duplicate
  version-numbered playlists.

## Design notes

A mixtape is the opposite of an algorithmic playlist: it's *authored*. You bring the
taste; the agent does the hours of picking, matching, and sequencing you never have
time for. The goal is the feeling of "this playlist is MINE."

## Three modes

| Mode | Say something like |
|---|---|
| **Quick order** | "Make me a rainy-Sunday jazz playlist, 25 tracks, Spotify" |
| **Seed expansion** | "I like two kinds of rock — these 2 songs are one kind, these 2 are the other. Expand to 30." |
| **Taste profile** | "Here are my existing playlists — figure out what I actually like, then curate for me." |

The taste profile persists in `~/.mixtape/` (plain Markdown, stays on your machine).
Over time the agent blends songs you already love with adjacent discoveries — and
remembers what failed to match and what you vetoed.

## Install

Install the standalone skill with the Skills CLI:

```bash
npx skills add m1nga/mixtape
```

Or clone it directly for a specific agent:

```bash
git clone https://github.com/m1nga/mixtape.git ~/.agents/skills/mixtape
```

Then just ask for a playlist in a session — no command to memorize.

**Requirements** — YouTube needs an authorized signed-in browser or equivalent
account access. Soundiiz imports use `curl`, `python3`, and a Soundiiz account
connected to the chosen music service.

## Soundiiz destinations

Use these settings when the user requests an import link.

| Platform | Import link preselect |
|---|---|
| Apple Music | `applemusicapp` |
| Spotify | `spotify` |
| YouTube Music | `ytmusic` |
| YouTube, Deezer, Tidal | `youtube`, `deezer`, `tidal` |
| Choose in Soundiiz | Leave the destination unset |

## How Soundiiz imports work

The agent generates and sequences the tracklist (real, released recordings only —
it verifies when unsure), then checks every title+artist pair against the requested
Apple Music storefront. The canonicalizer writes the official display metadata, a
catalog evidence report, and a fingerprint. Only that fingerprinted payload can reach
Soundiiz's free, key-less Playlist Import API.

The Soundiiz contract is deliberately enforced at the last mile: its field is
`artists` (plural), as an array or string. Sending `artist` appears to work because
the endpoint accepts the JSON, but the artist is silently ignored and matching
falls back to the title alone. Mixtape migrates legacy payloads but never sends the
wrong field.

You get a link valid for 24 hours; the confirmation click doubles as your
preview/veto step. Limits: ≤200 tracks per link and 10 requests/min.

For Apple Music on macOS, the included reconciliation helper inventories the local
library, dry-runs an exact-ID plan, then (only with `--apply`) renames the retained
playlist, deletes explicitly named predecessors, and reads the library back. It
refuses stale names, unexpected track counts, and unrelated playlists that happen
to share the final title. Optional protected IDs are also checked and returned as
unchanged in the final receipt.

## Field-tested

The bug that prompted the strict pipeline was a two-hour running mix where only
8/33 tracks transferred despite Apple Music carrying almost all of them. The first
“fix” reported 0 unconfirmed but had actually changed `The Less I Know the Better —
Tame Impala` into a similarly titled song by ALB and `Raw Control — Discip` into a
DubMabs track. The revised matcher now rejects both cases, blocks the post, and
shows the catalog evidence needed to choose a real replacement. The verified
replacement imported all 33 tracks; the final read-back kept one 33-track playlist
named `跑步` and removed the two superseded managed versions.

## 中文说明

Mixtape 可以按场景、种子歌或听歌口味编排歌单。指定 YouTube 或 YouTube Music
时，它用已授权的账号保存精准的录音，再打开歌单核对每首和顺序，最后给出正式链接。
用 Soundiiz 导入 Apple Music、Spotify 等服务时，它先核对 Apple Music 曲库，再给出
导入入口。口味档案和歌单历史保存在本机 `~/.mixtape/`。

## Notes

- Not affiliated with Soundiiz; uses their public Playlist Import API.
- Song selection quality depends on the model running the skill.
- Local taste files are not uploaded by the bundled scripts. Catalog lookups send
  song queries to Apple; Soundiiz receives the playlist title, description,
  destination and `{title, artists}` entries. Your agent provider also processes
  what you put in the conversation.

MIT © [m1nga](https://github.com/m1nga)

## YouTube playlist verification

For a saved playlist, Mixtape pins the intended video IDs, edits the existing
playlist or creates one private playlist, then reopens it from the target account.
It compares every saved ID in order, including repeats. The saved URL and verified
count identify the result. YouTube Music is checked in its own library because
it can show fewer items than YouTube. [YouTube Music help](https://support.google.com/youtubemusic/answer/7205933)

In a live maintainer run, an existing private playlist contained one of twelve
intended tracks. The agent added the other eleven by exact watch URL through
YouTube's own **Add videos** picker and reopened the same playlist from the
account library. All twelve video IDs and positions matched. No account or
playlist identifiers are included in this example.

See the [YouTube workflow](skills/mixtape/SKILL.md#youtube-saved-playlists) and
[YouTube's playlist help](https://support.google.com/youtube/answer/57792).

For Soundiiz imports, Apple catalog verification covers recording identity in
the selected storefront. The import response shows how many tracks Soundiiz
accepted. Completion depends on the result in the chosen destination.

Run `python3 -m unittest discover -s tests -v` from the installed skill directory
to check matching, partial import acceptance, ordered YouTube comparisons and
exact-ID reconciliation with fixtures.

## Author

Built by [Ming](https://github.com/m1nga). The design notes above explain the real problem and tradeoffs that shaped this skill.

<!-- sidecourt-referral:start -->
## Explore SideCourt

A playlist is a made thing too. [Browse SideCourt](https://sidecourt.space/drops/?utm_source=github&utm_medium=readme&utm_campaign=tools&utm_content=mixtape) to discover shared work, or share a mix with the scene, story or listening feedback you have in mind.
<!-- sidecourt-referral:end -->
