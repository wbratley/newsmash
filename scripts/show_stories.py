#!/usr/bin/env python3
"""Print today's top stories with per-outlet bias analysis."""

import sys
import textwrap
import httpx

BASE_URL = "http://localhost:8000"

LEAN_LABEL = {
    "left": "left",
    "centre-left": "centre-left",
    "centre": "centre",
    "centre-right": "centre-right",
    "right": "right",
}

WIDTH = 72
INDENT = "    "


def wrap(text: str, indent: str = INDENT) -> str:
    return textwrap.fill(text, width=WIDTH, initial_indent=indent, subsequent_indent=indent)


def main() -> None:
    print(f"Fetching today's stories from {BASE_URL} ...\n")
    try:
        r = httpx.get(f"{BASE_URL}/news/today", timeout=120)
        r.raise_for_status()
    except httpx.ConnectError:
        sys.exit("Error: server not running at " + BASE_URL)

    data = r.json()
    print(f"Generated: {data['generated_at']}  |  Clusters: {data['cluster_count']}\n")
    print("=" * WIDTH)

    for i, cluster in enumerate(data["clusters"], 1):
        print(f"\n#{i}  {cluster['neutral_headline']}\n")
        print(wrap(cluster["unbiased_summary"]))

        for outlet in cluster["outlets"]:
            lean = LEAN_LABEL.get(outlet["lean"], outlet["lean"])
            print(f"\n  {outlet['outlet'].upper()}  [{lean}]")
            print(wrap(f"Angle: {outlet['angle']}", indent=INDENT))
            print(wrap(f"Bias:  {outlet['bias_notes']}", indent=INDENT))
            for article in outlet["articles"]:
                print(f"{INDENT}• {article['headline']}")

        print("\n" + "-" * WIDTH)


if __name__ == "__main__":
    main()
