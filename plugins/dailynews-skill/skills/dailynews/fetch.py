#!/usr/bin/env python3
"""
dailynews/fetch.py — Standalone RSS + HTML headline fetcher
No external dependencies beyond Python stdlib.
"""

import sys
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import re
import time
from datetime import datetime, timezone
from html import unescape

SOURCES = [
    # (name, feed_url, type, category_hint)
    ("TechCrunch",          "https://techcrunch.com/feed/",                        "rss", "tech"),
    ("The Verge",           "https://www.theverge.com/rss/index.xml",              "rss", "tech"),
    ("Wired",               "https://www.wired.com/feed/rss",                      "rss", "tech"),
    ("MIT Tech Review",     "https://www.technologyreview.com/feed/",              "rss", "tech"),
    ("Hacker News",         "https://news.ycombinator.com/rss",                    "rss", "tech"),
    ("Product Hunt",        "https://www.producthunt.com/feed",                    "rss", "product"),
    ("Mind the Product",    "https://www.mindtheproduct.com/feed/",                "rss", "pm"),
    ("HBR",                 "https://hbr.org/feed",                                "rss", "pm"),
    ("Business Insider",    "https://feeds.businessinsider.com/custom/all",        "rss", "market"),
    ("Nielsen Norman",      "https://www.nngroup.com/feed/rss/",                   "rss", "design"),
    ("Stratechery",         "https://stratechery.com/feed/",                       "rss", "market"),
    ("Medium Technology",   "https://medium.com/feed/tag/technology",              "rss", "tech"),
    ("Medium Product",      "https://medium.com/feed/tag/product-management",      "rss", "pm"),
    ("Sensor Tower Blog",   "https://sensortower.com/blog/rss.xml",                "rss", "market"),
    ("Substack Tech",       "https://substack.com/browse/technology.rss",          "rss", "tech"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

def fetch_url(url, timeout=10):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            return content.decode(charset, errors="replace")
    except Exception as e:
        return None

def clean(text):
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def parse_rss(xml_text, source_name, category_hint):
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return articles

    ns = {"atom": "http://www.w3.org/2005/Atom"}

    # Handle both RSS and Atom formats
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//atom:entry", ns)
    if not items:
        items = root.findall(".//entry")

    for item in items[:20]:
        title_el = item.find("title")
        if title_el is None:
            title_el = item.find("atom:title", ns)
        link_el = item.find("link")
        if link_el is None:
            link_el = item.find("atom:link", ns)
        pub_el = item.find("pubDate")
        if pub_el is None:
            pub_el = item.find("published")
        if pub_el is None:
            pub_el = item.find("atom:published", ns)

        title = clean(title_el.text if title_el is not None else "")
        if not title or len(title) < 10:
            continue

        # Link can be text or href attribute (Atom)
        link = ""
        if link_el is not None:
            link = link_el.text or link_el.get("href", "") or ""
        link = link.strip()

        pub_date = ""
        if pub_el is not None:
            pub_date = (pub_el.text or "").strip()

        if title and link:
            articles.append({
                "title": title,
                "url": link,
                "source": source_name,
                "category_hint": category_hint,
                "pub_date": pub_date,
            })

    return articles

def fetch_all():
    results = []
    errors = []

    for name, url, feed_type, hint in SOURCES:
        sys.stderr.write(f"Fetching {name}... ")
        text = fetch_url(url)
        if text is None:
            sys.stderr.write("FAILED\n")
            errors.append({"source": name, "status": "UNAVAILABLE"})
            continue

        if feed_type == "rss":
            articles = parse_rss(text, name, hint)
        else:
            articles = []

        sys.stderr.write(f"{len(articles)} articles\n")
        results.extend(articles)
        time.sleep(0.3)  # be polite

    return results, errors

def deduplicate(articles):
    """Group articles by story similarity using keyword overlap."""
    groups = []
    used = set()

    for i, a in enumerate(articles):
        if i in used:
            continue
        group = [a]
        used.add(i)
        words_a = set(re.findall(r'\b[A-Za-z]{4,}\b', a["title"].lower()))

        for j, b in enumerate(articles):
            if j in used or j == i:
                continue
            words_b = set(re.findall(r'\b[A-Za-z]{4,}\b', b["title"].lower()))
            overlap = len(words_a & words_b)
            # 3+ common significant words = same story
            if overlap >= 3:
                group.append(b)
                used.add(j)

        groups.append(group)

    # Build deduplicated list
    deduped = []
    for group in groups:
        # Pick the longest/most descriptive title as canonical
        canonical = max(group, key=lambda x: len(x["title"]))
        sources = list({a["source"]: a["url"] for a in group}.items())
        deduped.append({
            "title": canonical["title"],
            "sources": sources,
            "source_count": len(sources),
            "category_hint": canonical["category_hint"],
            "pub_date": canonical["pub_date"],
        })

    return deduped

if __name__ == "__main__":
    all_articles, errors = fetch_all()
    deduped = deduplicate(all_articles)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_raw": len(all_articles),
        "total_unique": len(deduped),
        "articles": deduped,
        "errors": errors,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
