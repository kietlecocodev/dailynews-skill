# dailynews-skill

A Claude Code skill that fetches daily tech news from 15+ RSS sources, deduplicates stories, categorizes them into 4 buckets, writes a Vietnamese digest (~10 min read), and saves it to Notion automatically.

## What it does

- Fetches headlines from TechCrunch, The Verge, Wired, MIT Tech Review, Hacker News, Product Hunt, Nielsen Norman, Stratechery, Business Insider, and more
- Deduplicates cross-source stories and ranks by coverage
- Categorizes into: 🚀 Tech trends · 🧠 Product management · 📊 Market analysis · 🎨 UX/Design
- Outputs a Vietnamese digest with tier badges (🔥 Hot / 📌 Notable / 💡 Worth Reading)
- Saves locally to `~/.dailynews/YYYY-MM-DD.md`
- Auto-pushes to a Notion "Daily news" parent page

## Usage

In Claude Code, run:

```
/dailynews
```

## Installation

1. Copy `SKILL.md` and `fetch.py` to `~/.claude/skills/dailynews/`
2. Requires Python 3 (`brew install python3`)
3. Requires Notion MCP connected in Claude Code for auto-Notion push

## Files

- `SKILL.md` — Skill definition loaded by Claude Code
- `fetch.py` — RSS fetcher with deduplication logic
