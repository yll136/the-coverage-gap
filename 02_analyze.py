"""
THE COVERAGE GAP - Step 2: Analyze & Visualize
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BG = "#0d1117"
GRID = "#21262d"
TEXT = "#e6edf3"
DIM = "#7d8590"
RED = "#f85149"
BLUE = "#58a6ff"

CCOLORS = {
    "Ukraine": "#f85149", "Palestine/Gaza": "#58a6ff", "Congo (DRC)": "#3fb950",
    "Sudan": "#d29922", "Yemen": "#f778ba", "Myanmar": "#bc8cff",
    "Ethiopia/Tigray": "#39d2c0", "Somalia": "#e3b341",
}

LEGEND = [Patch(facecolor="#f85149", label="white-majority"), Patch(facecolor="#58a6ff", label="POC-majority")]


def style(ax, title, sub):
    ax.set_facecolor(BG)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=DIM, labelsize=10)
    ax.set_title(title, fontsize=22, fontweight="bold", color=TEXT, loc="left", pad=30, fontfamily="serif")
    ax.text(0, 1.01, sub, transform=ax.transAxes, fontsize=10, color=DIM, fontfamily="monospace", va="bottom")


def add_legend(ax, loc="lower right"):
    ax.legend(handles=LEGEND, loc=loc, fontsize=9, framealpha=0.3, edgecolor=GRID, facecolor=BG, labelcolor=DIM)


def plot_total_coverage(df):
    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(BG)
    df = df.sort_values("total_articles", ascending=True)
    y = np.arange(len(df))
    colors = [RED if p == "white" else BLUE for p in df["population"]]
    bars = ax.barh(y, df["total_articles"], color=colors, height=0.55, alpha=0.85, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(df["conflict"], fontsize=12, fontfamily="serif", color=TEXT)
    for bar, val in zip(bars, df["total_articles"]):
        ax.text(bar.get_width() + 8, bar.get_y() + bar.get_height() / 2,
                f"{val:,}", va="center", fontsize=11, color=DIM, fontfamily="monospace", fontweight="bold")
    style(ax, "The Coverage Gap", "Total headline articles · 15 selected mostly US outlets · Oct 2025 – Apr 2026")
    ax.xaxis.grid(True, color=GRID, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    add_legend(ax)
    plt.tight_layout(pad=2)
    plt.savefig(os.path.join(OUTPUT_DIR, "total_coverage.png"), dpi=200, bbox_inches="tight", facecolor=BG)
    print("[+] total_coverage.png")
    plt.close()


def plot_coverage_per_death(df):
    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(BG)
    df = df.sort_values("articles_per_death", ascending=True)
    y = np.arange(len(df))
    colors = [RED if p == "white" else BLUE for p in df["population"]]
    bars = ax.barh(y, df["articles_per_death"], color=colors, height=0.55, alpha=0.85, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(df["conflict"], fontsize=12, fontfamily="serif", color=TEXT)
    for bar, val in zip(bars, df["articles_per_death"]):
        ax.text(bar.get_width() + 0.0005, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=10, color=DIM, fontfamily="monospace")
    style(ax, "Who Gets Mourned?", "Articles per civilian death · title-verified results")
    ax.xaxis.grid(True, color=GRID, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    add_legend(ax)
    plt.tight_layout(pad=2)
    plt.savefig(os.path.join(OUTPUT_DIR, "coverage_per_death.png"), dpi=200, bbox_inches="tight", facecolor=BG)
    print("[+] coverage_per_death.png")
    plt.close()


def plot_coverage_multiplier(df):
    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(BG)
    ukraine_cpd = df.loc[df["conflict"] == "Ukraine", "articles_per_death"].values[0]
    others = df[df["conflict"] != "Ukraine"].copy()
    others["multiplier"] = ukraine_cpd / others["articles_per_death"]
    others = others.sort_values("multiplier", ascending=True)
    y = np.arange(len(others))
    max_m = others["multiplier"].max()
    bars = ax.barh(y, others["multiplier"], color=BLUE, height=0.55, zorder=3)
    for bar, m in zip(bars, others["multiplier"]):
        bar.set_alpha(0.4 + 0.6 * (m / max_m))
    ax.set_yticks(y)
    ax.set_yticklabels(others["conflict"], fontsize=12, fontfamily="serif", color=TEXT)
    for bar, val in zip(bars, others["multiplier"]):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}×", va="center", fontsize=14, fontweight="bold", color=RED, fontfamily="monospace")
    style(ax, "The Multiplier", "Times more coverage per death Ukraine receives vs. each conflict")
    ax.xaxis.grid(True, color=GRID, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout(pad=2)
    plt.savefig(os.path.join(OUTPUT_DIR, "coverage_multiplier.png"), dpi=200, bbox_inches="tight", facecolor=BG)
    print("[+] coverage_multiplier.png")
    plt.close()


def plot_timeline(tl):
    fig, ax = plt.subplots(figsize=(16, 7))
    fig.patch.set_facecolor(BG)
    fig.subplots_adjust(right=0.88)
    label_points = []
    label_x = None
    for conflict in tl["conflict"].unique():
        subset = tl[tl["conflict"] == conflict].copy()
        subset["date"] = pd.to_datetime(subset["date"])
        subset = subset.sort_values("date")
        subset["smooth"] = subset["count"].rolling(7, min_periods=1).mean()
        color = CCOLORS.get(conflict, DIM)
        major = conflict in ["Ukraine", "Palestine/Gaza"]
        ax.plot(subset["date"], subset["smooth"], color=color, label=conflict,
                linewidth=2.5 if major else 1.2, alpha=1.0 if major else 0.5, zorder=3 if major else 2)
        last_y = float(subset["smooth"].iloc[-1])
        last_x = subset["date"].iloc[-1]
        label_x = last_x + pd.Timedelta(days=6)
        label_points.append({
            "conflict": conflict,
            "y": last_y,
            "color": color,
            "major": major,
        })

    label_points = sorted(label_points, key=lambda x: x["y"])
    min_gap = 0.28
    for i in range(1, len(label_points)):
        if label_points[i]["y"] - label_points[i - 1]["y"] < min_gap:
            label_points[i]["y"] = label_points[i - 1]["y"] + min_gap

    upper_cap = max(max(p["y"] for p in label_points) + 0.35, ax.get_ylim()[1])
    for i in range(len(label_points) - 2, -1, -1):
        if upper_cap - label_points[i]["y"] < min_gap * (len(label_points) - 1 - i):
            label_points[i]["y"] = label_points[i + 1]["y"] - min_gap

    for point in label_points:
        ax.text(label_x, point["y"], point["conflict"],
                fontsize=9 if point["major"] else 7, color=point["color"], fontfamily="monospace",
                va="center", alpha=0.95 if point["major"] else 0.75,
                fontweight="bold" if point["major"] else "normal", clip_on=False)

    ax.set_xlim(pd.to_datetime(tl["date"].min()), pd.to_datetime(tl["date"].max()) + pd.Timedelta(days=18))
    style(ax, "Who Gets Covered?", "Daily articles · 7-day rolling avg · 15 selected mostly US outlets")
    ax.xaxis.grid(True, color=GRID, alpha=0.3, zorder=0)
    ax.yaxis.grid(True, color=GRID, alpha=0.3, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylabel("articles / day", fontsize=10, color=DIM, fontfamily="monospace")
    plt.savefig(os.path.join(OUTPUT_DIR, "timeline_comparison.png"), dpi=200, bbox_inches="tight", facecolor=BG)
    print("[+] timeline_comparison.png")
    plt.close()


def plot_deaths_vs_coverage(df):
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor(BG)

    max_articles = df["total_articles"].max()

    for _, row in df.iterrows():
        color = RED if row["population"] == "white" else BLUE
        ax.scatter(row["est_civilian_deaths"], row["total_articles"],
                   c=color, s=160, alpha=0.85, edgecolors="white", linewidth=0.8, zorder=3)
        ox, oy = 10, 12
        if row["conflict"] == "Yemen":
            ox, oy = 10, -18
        elif row["conflict"] == "Somalia":
            ox, oy = 10, 18
        elif row["conflict"] == "Congo (DRC)":
            ox, oy = 10, 14
        elif row["conflict"] == "Ethiopia/Tigray":
            ox, oy = -90, 14
        ax.annotate(row["conflict"],
                    (row["est_civilian_deaths"], row["total_articles"]),
                    xytext=(ox, oy), textcoords="offset points",
                    fontsize=10, color=DIM, fontfamily="serif")

    style(ax, "The Disconnect", "Civilian deaths vs. media coverage · each dot is a conflict")
    ax.set_xscale("log")
    ax.set_xlabel("estimated civilian deaths (log scale)", fontsize=10, color=DIM, fontfamily="monospace")
    ax.set_ylabel("total articles", fontsize=10, color=DIM, fontfamily="monospace")
    ax.xaxis.grid(True, color=GRID, alpha=0.3, zorder=0)
    ax.yaxis.grid(True, color=GRID, alpha=0.3, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylim(-20, max_articles * 1.3)
    ax.set_xlim(3000, 500000)
    add_legend(ax, loc="upper right")
    plt.tight_layout(pad=2)
    plt.savefig(os.path.join(OUTPUT_DIR, "deaths_vs_coverage.png"), dpi=200, bbox_inches="tight", facecolor=BG)
    print("[+] deaths_vs_coverage.png")
    plt.close()


def export_json(counts, timeline):
    d = {"conflicts": [], "timeline": {}}
    for _, r in counts.iterrows():
        d["conflicts"].append({"name": r["conflict"], "articles": int(r["total_articles"]),
            "deaths": int(r["est_civilian_deaths"]), "articles_per_death": float(r["articles_per_death"]),
            "population": r["population"], "region": r["region"]})
    for c in timeline["conflict"].unique():
        s = timeline[timeline["conflict"] == c]
        d["timeline"][c] = [{"date": r["date"], "count": int(r["count"])} for _, r in s.iterrows()]
    with open(os.path.join(OUTPUT_DIR, "dashboard_data.json"), "w") as f:
        json.dump(d, f, indent=2)
    print("[+] dashboard_data.json")


def main():
    print("=" * 60)
    print("THE COVERAGE GAP — Analysis & Visualization")
    print("=" * 60)
    counts = pd.read_csv(os.path.join(DATA_DIR, "article_counts.csv"))
    timeline = pd.read_csv(os.path.join(DATA_DIR, "coverage_over_time.csv"))
    print(f"[*] {len(counts)} conflicts, {len(timeline)} timeline rows\n")

    ukraine = counts[counts["conflict"] == "Ukraine"].iloc[0]
    for _, r in counts.sort_values("articles_per_death", ascending=False).iterrows():
        if r["conflict"] != "Ukraine" and r["articles_per_death"] > 0:
            ratio = ukraine["articles_per_death"] / r["articles_per_death"]
            print(f"  Ukraine → {ratio:.0f}× more coverage/death than {r['conflict']}")

    print("\n[*] Generating charts...")
    plot_total_coverage(counts)
    plot_coverage_per_death(counts)
    plot_coverage_multiplier(counts)
    plot_timeline(timeline)
    plot_deaths_vs_coverage(counts)
    export_json(counts, timeline)

    worst = counts.sort_values("articles_per_death").iloc[0]
    ratio = ukraine["articles_per_death"] / worst["articles_per_death"]
    print(f"\n{'=' * 60}")
    print(f"HEADLINE: {ratio:.0f}× more coverage per death")
    print(f"  Ukraine vs {worst['conflict']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
