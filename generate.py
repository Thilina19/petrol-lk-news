import os
import json
import html
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
import feedparser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

def ensure_dirs():
    os.makedirs(PUBLIC_DIR, exist_ok=True)

def parse_date(entry):
    candidates = [entry.get("published"), entry.get("updated")]
    for c in candidates:
        if c:
            try:
                dt = parsedate_to_datetime(c)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)

def source_host(link):
    try:
        return urlparse(link).netloc.replace("www.", "")
    except Exception:
        return ""

def load_feeds():
    with open(os.path.join(BASE_DIR, "feeds.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def collect_items(feeds):
    items = []
    seen_links = set()

    for feed in feeds:
        parsed = feedparser.parse(feed["url"])
        for e in parsed.entries[:20]:
            link = e.get("link", "").strip()
            title = e.get("title", "").strip()

            if not link or not title:
                continue
            if link in seen_links:
                continue
            seen_links.add(link)

            summary = e.get("summary", "") or e.get("description", "")
            summary = summary.replace("<br>", " ").replace("<br/>", " ")
            summary = summary[:280]

            dt = parse_date(e)

            items.append({
                "title": title,
                "link": link,
                "summary": summary,
                "category": feed.get("category", "news"),
                "feed_name": feed.get("name", "News"),
                "source_host": source_host(link),
                "published_utc": dt.isoformat(),
                "published_sort": dt.timestamp()
            })

    items.sort(key=lambda x: x["published_sort"], reverse=True)
    return items[:120]

def group_items(items):
    groups = {
        "sri-lanka-motorsport": [],
        "sri-lanka-automotive": [],
        "global-motorsport": [],
        "global-automotive": []
    }
    for item in items:
        groups.setdefault(item["category"], []).append(item)
    return groups

def render_list(items):
    rows = []
    for item in items:
        title = html.escape(item["title"])
        summary = item["summary"] or ""
        summary = summary.replace("<", "").replace(">", "")
        summary = html.escape(summary)
        published = item["published_utc"].replace("T", " ").replace("+00:00", " UTC")
        rows.append(f"""
        <article class="card">
          <div class="meta">
            <span class="tag">{html.escape(item["feed_name"])}</span>
            <span>{html.escape(item["source_host"])}</span>
            <span>{html.escape(published)}</span>
          </div>
          <h3><a href="{html.escape(item["link"])}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
          <p>{summary}</p>
          <a class="readmore" href="{html.escape(item["link"])}" target="_blank" rel="noopener noreferrer">Read full article</a>
        </article>
        """)
    return "\n".join(rows) if rows else '<p class="empty">No items yet. Check feeds.json.</p>'

def build_html(items):
    groups = group_items(items)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Petrol.lk | Sri Lanka Automotive & Motorsport News</title>
  <meta name="description" content="Live updates on Sri Lanka automotive and motorsport news, plus global racing headlines." />
  <style>
    body {{ font-family: Arial, sans-serif; margin:0; background:#0b0f14; color:#e8edf2; }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
    header {{ padding: 18px 0 6px; }}
    h1 {{ margin: 0 0 6px; font-size: 30px; }}
    .sub {{ color:#9fb0c3; margin:0 0 18px; }}
    .grid {{ display:grid; grid-template-columns:1fr; gap:18px; }}
    @media (min-width: 900px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
    section {{ background:#121923; border:1px solid #223041; border-radius:14px; padding:14px; }}
    section h2 {{ margin: 0 0 10px; font-size: 20px; }}
    .card {{ background:#0f151e; border:1px solid #1f2a38; border-radius:10px; padding:12px; margin-bottom:10px; }}
    .card h3 {{ margin:6px 0 8px; font-size:16px; line-height:1.35; }}
    .card h3 a {{ color:#e8edf2; text-decoration:none; }}
    .card h3 a:hover {{ text-decoration:underline; }}
    .card p {{ margin:0 0 8px; color:#bfd0e2; font-size:14px; line-height:1.5; }}
    .meta {{ display:flex; flex-wrap:wrap; gap:8px; font-size:12px; color:#93a4b7; }}
    .tag {{ background:#1c2938; border:1px solid #2d4158; padding:2px 8px; border-radius:999px; }}
    .readmore {{ font-size:13px; color:#7fc4ff; text-decoration:none; }}
    .readmore:hover {{ text-decoration:underline; }}
    footer {{ color:#93a4b7; font-size:13px; padding:16px 0 30px; }}
    .empty {{ color:#93a4b7; }}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Petrol.lk</h1>
      <p class="sub">Sri Lanka-focused automotive and motorsport updates + global racing headlines</p>
      <p class="sub">Auto-generated: {generated}</p>
    </header>

    <div class="grid">
      <section>
        <h2>Sri Lanka Motorsport</h2>
        {render_list(groups.get("sri-lanka-motorsport", [])[:20])}
      </section>

      <section>
        <h2>Sri Lanka Automotive</h2>
        {render_list(groups.get("sri-lanka-automotive", [])[:20])}
      </section>

      <section>
        <h2>Global Motorsport</h2>
        {render_list(groups.get("global-motorsport", [])[:20])}
      </section>

      <section>
        <h2>Global Automotive</h2>
        {render_list(groups.get("global-automotive", [])[:20])}
      </section>
    </div>

    <footer>
      Petrol.lk aggregates headlines and links to original sources. Click through to read full articles.
    </footer>
  </div>
</body>
</html>
"""

def main():
    ensure_dirs()
    feeds = load_feeds()
    items = collect_items(feeds)

    with open(os.path.join(PUBLIC_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_html(items))

    with open(os.path.join(PUBLIC_DIR, "news.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
