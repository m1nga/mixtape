# Mixtape 🎧

**Your own playlist, made by your AI.**

Everyone's library is full of playlists made by strangers and algorithms. Mixtape is
an [agent skill](https://www.thepromptindex.com/how-to-use-ai-agent-skills-the-complete-guide.html)
for **Claude Code** and **OpenAI Codex** that turns a described mood, a handful of
seed songs, or your actual listening taste into a real playlist in your streaming
account — delivered as a one-click [Soundiiz](https://soundiiz.com) import link.
No platform API keys, no developer accounts.

> "Playlist for cooking on a Friday night, city pop, ~20 tracks, YouTube Music"
> → a numbered tracklist with an arc, and a link. Open → confirm → it's in your library.

## Why "Mixtape"

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

**Claude Code**

```bash
git clone https://github.com/m1nga/mixtape.git ~/.claude/skills/mixtape
```

**OpenAI Codex** (skills support since Dec 2025)

```bash
git clone https://github.com/m1nga/mixtape.git ~/.agents/skills/mixtape
```

Then just ask for a playlist in a session — no command to memorize.

**Requirements**: `curl` + `python3` (present on macOS/Linux by default), and a free
[Soundiiz](https://soundiiz.com) account with your streaming platform connected
(that's where the import authorization lives).

## Supported destinations

| Platform | Import link preselect |
|---|---|
| Spotify, YouTube Music, YouTube, Deezer, Tidal | ✅ preselected |
| Apple Music | one extra tap on the import page |

## How it works

The agent generates and sequences the tracklist (real, released recordings only —
it verifies when unsure), then POSTs it to Soundiiz's free, key-less
[Playlist Import API](https://soundiiz.com/api/doc/public_import). You get back a
link valid for 24 hours; the confirmation click on the import page doubles as your
preview/veto step. Limits: ≤200 tracks per link (auto-split into volumes),
10 requests/min.

## 中文说明

Mixtape 是给 Claude Code / Codex 用的歌单 skill：一句话描述场景（「周五晚做饭的
City Pop，20首」）、或给几首种子歌（「我喜欢的摇滚分这两种……照这个扩展30首」）、
或让它分析你现有歌单的口味，它选歌、编排顺序，然后给你一个 Soundiiz 一键导入
链接——点开、确认、歌单进你的 Apple Music / YouTube Music。口味档案存在本机
`~/.mixtape/`，越用越懂你。安装：把仓库 clone 到 `~/.claude/skills/mixtape`
（Claude Code）或 `~/.agents/skills/mixtape`（Codex），需要一个免费 Soundiiz
账号并连接你的流媒体平台。

## Notes

- Not affiliated with Soundiiz; uses their public Playlist Import API.
- Song selection quality depends on the model running the skill.
- Taste data never leaves your machine — only `{title, artist}` lists are sent to
  Soundiiz to build the import link.

MIT © [m1nga](https://github.com/m1nga)
