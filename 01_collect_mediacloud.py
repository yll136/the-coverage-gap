"""
THE COVERAGE GAP - Data Collection via MediaCloud
Title-only search to ensure articles are ABOUT the conflict.
15 specific outlets, 6 months, English only.

Usage: python3 01_collect_mediacloud.py
"""

import requests
import pandas as pd
import time
import os

MC_API_KEY = os.getenv("MEDIACLOUD_API_KEY")
BASE_URL = "https://search.mediacloud.org/api"
START_DATE = "2025-10-01"
END_DATE = "2026-04-01"

OUTLETS = [
    "cnn.com", "nytimes.com", "foxnews.com", "bbc.com",
    "washingtonpost.com", "nbcnews.com", "cbsnews.com",
    "abcnews.go.com", "apnews.com", "reuters.com",
    "usatoday.com", "npr.org", "msnbc.com",
    "politico.com", "thehill.com",
]
DOMAIN_FILTER = "(" + " OR ".join([f"canonical_domain:{d}" for d in OUTLETS]) + ")"

# TITLE-ONLY QUERIES using article_title: prefix
# This ensures the article is actually ABOUT the conflict,
# not just mentioning it in passing
CONFLICTS = {
    "Ukraine": {
        "terms": 'article_title:ukraine AND article_title:(war OR killed OR civilian OR casualties OR attack OR invasion OR troops)',
        "population": "white", "region": "Europe", "est_deaths": 12910,
    },
    "Palestine": {
        "terms": 'article_title:(palestine OR gaza) AND article_title:(war OR killed OR civilian OR casualties OR attack OR strike OR death)',
        "population": "poc", "region": "Middle East", "est_deaths": 70000,
    },
    "Congo (DRC)": {
        "terms": 'article_title:(congo OR DRC OR goma) AND article_title:(war OR killed OR conflict OR violence OR attack OR rebel)',
        "population": "poc", "region": "Africa", "est_deaths": 120000,
    },
    "Sudan": {
        "terms": 'article_title:sudan AND article_title:(war OR killed OR RSF OR conflict OR darfur OR attack OR crisis)',
        "population": "poc", "region": "Africa", "est_deaths": 25000,
    },
    "Yemen": {
        "terms": 'article_title:yemen AND article_title:(war OR killed OR houthi OR strike OR civilian OR attack OR conflict)',
        "population": "poc", "region": "Middle East", "est_deaths": 15000,
    },
    "Myanmar": {
        "terms": 'article_title:(myanmar OR rohingya) AND article_title:(war OR killed OR conflict OR military OR junta OR attack)',
        "population": "poc", "region": "Asia", "est_deaths": 7700,
    },
    "Ethiopia/Tigray": {
        "terms": 'article_title:(tigray OR ethiopia) AND article_title:(war OR killed OR conflict OR attack OR crisis)',
        "population": "poc", "region": "Africa", "est_deaths": 300000,
    },
    "Somalia": {
        "terms": 'article_title:somalia AND article_title:(al-shabaab OR killed OR attack OR conflict OR war OR bombing)',
        "population": "poc", "region": "Africa", "est_deaths": 5000,
    },
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

if not MC_API_KEY:
    raise ValueError("Set the MEDIACLOUD_API_KEY environment variable before running this script.")

HEADERS = {"Authorization": f"Token {MC_API_KEY}"}


def build_query(terms):
    return f"({terms}) AND {DOMAIN_FILTER}"


def main():
    print("=" * 60)
    print("THE COVERAGE GAP — MediaCloud Data Collection")
    print("TITLE-ONLY SEARCH — articles must be ABOUT the conflict")
    print(f"Date range: {START_DATE} to {END_DATE} (6 months)")
    print(f"Sources: {len(OUTLETS)} outlets only")
    print("=" * 60)

    all_timeline = []
    counts = []

    for i, (name, c) in enumerate(CONFLICTS.items(), 1):
        query = build_query(c["terms"])
        print(f"\n[{i}/{len(CONFLICTS)}] {name}")

        try:
            params = {
                "q": query, "start": START_DATE, "end": END_DATE,
                "platform": "onlinenews-mediacloud",
            }
            resp = requests.get(f"{BASE_URL}/search/count-over-time",
                                params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            points = data.get("count_over_time", {}).get("counts", [])
            total = sum(p.get("count", 0) for p in points)

            for p in points:
                all_timeline.append({
                    "conflict": name, "date": p.get("date", ""),
                    "count": p.get("count", 0),
                    "total_count": p.get("total_count", 0),
                    "ratio": p.get("ratio", 0),
                    "population": c["population"], "region": c["region"],
                })

            print(f"    ✓ {len(points)} days, {total:,} total articles")

        except Exception as e:
            print(f"    ✗ Error: {e}")
            total = 0

        counts.append({
            "conflict": name, "total_articles": total,
            "population": c["population"], "region": c["region"],
            "est_civilian_deaths": c["est_deaths"],
            "articles_per_death": round(total / c["est_deaths"], 4) if c["est_deaths"] > 0 else 0,
        })

        time.sleep(3)

    # Fetch article samples for validation (one at a time, with delays)
    print("\n[*] Fetching article samples for validation...")
    all_articles = []
    for name in list(CONFLICTS.keys())[:4]:  # Top 4 only
        c = CONFLICTS[name]
        query = build_query(c["terms"])
        try:
            params = {
                "q": query, "start": START_DATE, "end": END_DATE,
                "platform": "onlinenews-mediacloud",
            }
            resp = requests.get(f"{BASE_URL}/search/story-list",
                                params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            stories = data if isinstance(data, list) else data.get("stories", data.get("results", []))
            print(f"    {name}: {len(stories)} articles")
            for s in stories[:3]:
                src = s.get("media_name", s.get("canonical_domain", ""))
                title = s.get("title", s.get("article_title", ""))[:70]
                print(f"      → [{src}] {title}")
            for s in stories[:100]:
                all_articles.append({
                    "conflict": name,
                    "title": s.get("title", s.get("article_title", "")),
                    "source": s.get("media_name", s.get("canonical_domain", "")),
                    "url": s.get("url", s.get("original_url", "")),
                    "publish_date": s.get("publish_date", s.get("publication_date", "")),
                    "population": c["population"],
                })
        except Exception as e:
            print(f"    {name}: error: {e}")
        time.sleep(5)

    # Save
    print("\n" + "-" * 40)
    if all_timeline:
        pd.DataFrame(all_timeline).to_csv(
            os.path.join(OUTPUT_DIR, "coverage_over_time.csv"), index=False)
        print(f"[+] Saved coverage_over_time.csv ({len(all_timeline)} rows)")

    counts_df = pd.DataFrame(counts).sort_values("total_articles", ascending=False)
    counts_df.to_csv(os.path.join(OUTPUT_DIR, "article_counts.csv"), index=False)
    print(f"[+] Saved article_counts.csv")

    if all_articles:
        pd.DataFrame(all_articles).to_csv(
            os.path.join(OUTPUT_DIR, "articles_sample.csv"), index=False)
        print(f"[+] Saved articles_sample.csv ({len(all_articles)} articles)")

    # Results
    print("\n" + "=" * 60)
    print("COVERAGE COMPARISON (TITLE-ONLY SEARCH)")
    print(f"15 Major Outlets, {START_DATE} to {END_DATE}")
    print("=" * 60)
    mx = counts_df["total_articles"].max() or 1
    for _, r in counts_df.iterrows():
        bar = "█" * int((r["total_articles"] / mx) * 30)
        p = "●" if r["population"] == "white" else "○"
        print(f"  {p} {r['conflict']:<20} {r['total_articles']:>6,} articles  {bar}")

    print("\n  COVERAGE PER CIVILIAN DEATH:")
    cpd = counts_df.sort_values("articles_per_death", ascending=False)
    for _, r in cpd.iterrows():
        print(f"    {r['conflict']:<20} {r['articles_per_death']:.4f}  "
              f"({r['total_articles']:,} articles / {r['est_civilian_deaths']:,} deaths)")

    top = cpd.iloc[0]
    for _, r in cpd.iterrows():
        if r["conflict"] != top["conflict"] and r["articles_per_death"] > 0:
            ratio = top["articles_per_death"] / r["articles_per_death"]
            if ratio > 2:
                print(f"\n  → {top['conflict']} gets {ratio:.0f}x more coverage "
                      f"per death than {r['conflict']}")

    print("\n  ● = white-majority  ○ = POC-majority")
    print("=" * 60)


if __name__ == "__main__":
    main()
