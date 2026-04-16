---
name: dailynews
version: 1.0.0
description: |
  Daily tech news digest in Vietnamese. Fetches headlines from 15 major tech/product/design
  RSS feeds (TechCrunch, The Verge, Wired, HN, Product Hunt, HBR, NNGroup, Stratechery, etc.),
  deduplicates cross-source stories, categorizes into 4 buckets, and outputs a ~10-minute
  ranked Vietnamese summary with source links. Fully standalone — no gstack required.
  Use when asked to "đọc tin", "tổng hợp tin tức", "daily news", "morning brief", or "/dailynews".
allowed-tools:
  - Bash
  - Read
  - Write
  - WebFetch
  - AskUserQuestion
  - mcp__claude_ai_Notion__notion-search
  - mcp__claude_ai_Notion__notion-create-pages
  - mcp__claude_ai_Notion__notion-fetch
---

## Overview

This is a fully self-contained skill. It uses:
- A bundled Python RSS fetcher (`fetch.py` in the same directory as this file)
- Claude's native `WebFetch` tool for any supplementary scraping
- No gstack, no external browser dependency

**Output:** A ranked Vietnamese digest (~10 min read), saved to `~/.dailynews/YYYY-MM-DD.md` and printed to the conversation.

---

## Step 1 — Setup

```bash
TODAY=$(date +%Y-%m-%d)
SKILL_DIR=$(dirname "$(find ~/.claude -path '*/skills/dailynews/SKILL.md' 2>/dev/null | head -1)")
FETCH_SCRIPT="$SKILL_DIR/fetch.py"
DIGEST_DIR="$HOME/.dailynews"
DIGEST_FILE="$DIGEST_DIR/$TODAY.md"
mkdir -p "$DIGEST_DIR"

echo "TODAY: $TODAY"
echo "SKILL_DIR: $SKILL_DIR"
echo "FETCH_SCRIPT: $FETCH_SCRIPT"
echo "DIGEST_FILE: $DIGEST_FILE"

# Check if today's digest already exists
[ -f "$DIGEST_FILE" ] && echo "CACHED: yes" || echo "CACHED: no"
```

If `CACHED` is `yes`: Ask the user:
- **A)** Show cached digest (instant)
- **B)** Re-fetch fresh news (takes ~1-2 min)

Default to **A** unless they explicitly choose B.

---

## Step 2 — Fetch RSS feeds

Run the bundled fetcher:

```bash
python3 "$FETCH_SCRIPT" 2>&1 | tee /tmp/dailynews_raw.json
```

If Python fails, try:
```bash
python "$FETCH_SCRIPT" 2>&1 | tee /tmp/dailynews_raw.json
```

Read the output:
```bash
cat /tmp/dailynews_raw.json
```

The output is a JSON object with:
- `total_raw` — total headlines scraped before dedup
- `total_unique` — unique stories after dedup
- `articles` — array of deduplicated story objects, each with:
  - `title` — canonical headline
  - `sources` — array of `[source_name, url]` pairs
  - `source_count` — how many sources covered this story
  - `category_hint` — rough hint: `tech`, `pm`, `market`, or `design`
  - `pub_date` — publication date string
- `errors` — sources that failed

If fewer than 3 sources responded, warn the user: "Chỉ có N nguồn phản hồi — kết quả có thể không đầy đủ. Tiếp tục?" and wait for confirmation.

---

## Step 3 — Supplement with WebFetch for sources not in RSS

Use the `WebFetch` tool to grab headlines from these sources that are not in the RSS list:

| Source | URL |
|--------|-----|
| Dribbble Popular | https://dribbble.com/shots/popular |
| Nielsen Norman Articles | https://www.nngroup.com/articles/ |
| Daily.dev | https://app.daily.dev (skip if auth wall) |

For each, call `WebFetch` with the URL and extract visible article titles and links from the page content. Add them to your working article list with appropriate category hints:
- Dribbble → `design`
- NNGroup → `design`
- Daily.dev → `tech`

---

## Step 4 — Categorize all stories

For each article in your working list, assign exactly one of the 4 categories below based on title keywords and `category_hint`. When in doubt, use the **primary subject** of the headline.

### Category A — 🚀 Xu hướng Công nghệ
**What:** AI models/products, new tech launches, SaaS releases, developer tools, funding rounds, acquisitions, open-source releases, platform updates, new products getting traction.

**Keywords to look for:** AI, LLM, model, launch, release, raises, funding, acquires, SaaS, API, open-source, developer, cloud, startup, GPT, Claude, Gemini, agent, automation

### Category B — 🧠 Tư duy Quản trị Sản phẩm
**What:** PM tactics, product strategy, feature frameworks, A/B testing, growth loops, product-led growth, roadmap methods, team structures, lessons learned, best practices for building products.

**Keywords:** product manager, roadmap, strategy, framework, growth, retention, onboarding, feature, sprint, prioritization, lesson, best practice, how to build, product thinking, OKR, metrics

### Category C — 📊 Phân tích Thị trường & Đối thủ
**What:** Big tech strategy moves, market share shifts, earnings reports, consumer behavior data, global mobile usage stats, M&A activity, regulatory/antitrust news, economic indicators affecting tech.

**Keywords:** market share, revenue, earnings, quarterly, billion, Apple, Google, Meta, Microsoft, Amazon, regulation, antitrust, download, DAU, MAU, users, global, report, study, data

### Category D — 🎨 Thiết kế & Trải nghiệm (UX/UI)
**What:** New UI design patterns, UX research, accessibility, design system updates, typography/motion trends, usability studies, Figma updates, design tool news.

**Keywords:** UX, UI, design, usability, accessibility, Figma, prototype, user research, interface, design system, typography, animation, interaction, visual design, color

---

## Step 5 — Rank within each category

Within each category, sort stories by:
1. `source_count` descending — more sources = higher rank
2. Tie-break: recency (more recent pub_date wins)
3. Stories from Stratechery, MIT Tech Review, HBR, NNGroup treated as authoritative single-source = weight 2

Assign tier badge:
- 🔥 **Hot** — 3+ sources
- 📌 **Notable** — 2 sources OR single authoritative source
- 💡 **Worth Reading** — 1 regular source

---

## Step 6 — Write the digest

Produce the full digest in this format. All narrative text in **Vietnamese**. Keep article titles in their original English (add a short Vietnamese gloss in parentheses when the title is jargon-heavy).

```markdown
# Tổng Hợp Tin Công Nghệ — {TODAY}
*Thời gian đọc: ~10 phút · {total_unique} tin từ {N} nguồn*

---

## 🚀 Xu hướng Công nghệ

**{tier_badge} {title}**
> {1-2 câu tóm tắt tiếng Việt — nêu điểm chính và tại sao quan trọng, max 50 từ}
🔗 {source_1}: {url_1}  {source_2}: {url_2}  ...

[repeat for each story in this category]

---

## 🧠 Tư duy Quản trị Sản phẩm

[same format]

---

## 📊 Phân tích Thị trường & Đối thủ

[same format]

---

## 🎨 Thiết kế & Trải nghiệm (UX/UI)

[same format]

---

## 📦 Sản phẩm mới hôm nay (Product Hunt)
*Top 5 theo upvotes*

1. **{product}** — {mô tả 1 câu tiếng Việt} 🔗 {url}
2. ...

---

*Nguồn thành công: {list} · Lỗi: {error list}*
*Cập nhật lúc: {timestamp}*
```

**Vietnamese summary rules:**
- 1-2 sentences per story, max 50 words
- Start with the most important fact, not "Theo bài viết..."
- Keep company names, product names, and numbers in original form
- For funding: always include amount + stage + investor if available
- For product launches: say what it does plainly
- For research: say the finding, not "a study found that..."

---

## Step 7 — Save locally and output

Use the `Write` tool to save the digest to `$DIGEST_FILE`.

Then print the full digest to the conversation.

---

## Step 8 — Save to Notion

After printing the digest, push it to Notion automatically.

### 8a — Generate the page name

The page title must follow the format: `dd/mm/yy - {name}`

Where `{name}` is a short (3-6 word) English descriptor of the day's top story or dominant theme. Examples:
- `03/04/25 - GPT-5 Launch & Apple Earnings`
- `03/04/25 - AI Agents Week`
- `03/04/25 - Meta Threads Hits 200M`

Pick the name from the #1 ranked story across all categories (the one with the highest `source_count`). If two stories tie, pick the most impactful one.

Format the date as `dd/mm/yy` using the `TODAY` variable:
```bash
NOTION_DATE=$(date +%d/%m/%y)
echo "NOTION_DATE: $NOTION_DATE"
```

### 8b — Find the "Daily news" parent page

Use `mcp__claude_ai_Notion__notion-search` with query `"Daily news"`.

Look for a page whose title is exactly or closely matches **"Daily news"**. Extract its `id` as `PARENT_PAGE_ID`.

If no match is found, ask the user:
> "Không tìm thấy trang 'Daily news' trong Notion. Bạn có muốn tôi tạo mới trang đó không, hay cung cấp ID trang parent?"

### 8c — Convert digest to Notion blocks

Map the digest markdown to Notion block format:

| Markdown | Notion block type |
|----------|-------------------|
| `# heading` | `heading_1` |
| `## heading` | `heading_2` |
| `**bold text**` | `paragraph` with bold annotation |
| `> blockquote` | `quote` |
| `🔗 Source: url` | `paragraph` with link |
| `---` | `divider` |
| numbered list | `numbered_list_item` |
| bullet `- item` | `bulleted_list_item` |
| plain paragraph | `paragraph` |

Build the `children` block array for the Notion page creation call.

**Important:** Notion API has a limit of 100 blocks per request. If the digest exceeds 100 blocks, split into multiple `notion-create-pages` or use `notion-update-page` calls. In practice, keep blocks under 95 to be safe.

### 8d — Create the child page

Call `mcp__claude_ai_Notion__notion-create-pages` with:
```json
{
  "parent": { "page_id": "{PARENT_PAGE_ID}" },
  "properties": {
    "title": [{ "text": { "content": "{NOTION_DATE} - {name}" } }]
  },
  "children": [ ... blocks array ... ]
}
```

### 8e — Confirm success

After the page is created, print:
```
✅ Đã lưu lên Notion: "{NOTION_DATE} - {name}"
🔗 {notion_page_url}
```

If Notion creation fails:
- Print the error
- Tell user: "Bản digest đã được lưu cục bộ tại ~/.dailynews/{TODAY}.md"
- Do NOT retry automatically — let user decide

---

## Step 9 — Final stats line

```
---
📈 {total_raw} headlines scraped → {total_unique} unique stories → {categorized} tiêu đề được xếp loại
📰 {N} nguồn thành công / 15+ · Lỗi/auth: {error_sources}
💾 Local: ~/.dailynews/{TODAY}.md
📓 Notion: {NOTION_DATE} - {name}
```

---

## Adding custom sources

To add a new RSS source, edit `~/.claude/skills/dailynews/fetch.py` and add a tuple to the `SOURCES` list:
```python
("Source Name", "https://example.com/feed.rss", "rss", "tech|pm|market|design"),
```

To add Datanleo or any custom source with a known RSS URL, add it to `SOURCES` in `fetch.py`.

---

## Error handling

| Error | Action |
|-------|--------|
| Python not found | Tell user to install Python 3: `brew install python3` |
| Source returns 403/401 | Mark `[AUTH_REQUIRED]`, skip |
| Source returns 5xx | Mark `[UNAVAILABLE]`, skip |
| JSON parse failure | Re-run fetch once, then skip if still failing |
| 0 articles total | Tell user all sources failed, suggest checking network |
| Cached digest exists | Ask A/B (show cached vs re-fetch) |

---

## Important rules

- Never fabricate news. Only use what was actually fetched.
- Every story must have at least one real URL.
- All prose output in Vietnamese. Titles stay in English.
- If a source is a paywall and only the title is visible, include it and mark `[paywall]`.
- Output goes directly to the conversation. Only the `.md` file is written to disk.
- Keep total digest length manageable: aim for 20-35 stories across all categories.
