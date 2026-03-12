"""
Fixed app explorer for AutonomousTester.

Crawls a web application using Playwright, discovers pages and interactive
elements (buttons, forms, inputs, links, headings), takes a screenshot of
each page, and writes a structured site_map.json for the agent to read.

The agent reads site_map.json before writing tests to understand:
  - Which pages/routes exist
  - What interactive elements are present on each page
  - What user flows might be testable

Usage:
    uv run explorer.py <URL>
    uv run explorer.py <URL> --depth 3 --max-pages 30

Output:
    site_map.json        — structured page inventory
    snapshots/explore_*  — full-page screenshots of each visited URL

DO NOT MODIFY THIS FILE.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SITE_MAP_FILE = "site_map.json"
SNAPSHOTS_DIR = Path("snapshots")
PAGE_LOAD_TIMEOUT = 15_000   # ms
NAV_TIMEOUT = 10_000         # ms

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def same_origin(url: str, base: str) -> bool:
    """Return True if url shares the same scheme+host as base."""
    p = urlparse(url)
    b = urlparse(base)
    return p.scheme == b.scheme and p.netloc == b.netloc


def url_to_slug(url: str, max_len: int = 60) -> str:
    """Convert a URL to a filesystem-safe slug for screenshot filenames."""
    slug = url.replace("://", "_").replace("/", "_").replace("?", "_").replace("=", "_")
    # Strip leading/trailing underscores and collapse sequences
    slug = "_".join(filter(None, slug.split("_")))
    return slug[:max_len]


def collect_page_elements(page) -> dict:
    """
    Harvest interactive elements visible on the current page.
    Returns a structured dict the agent can use to plan tests.
    """
    elements: dict = {}

    # Buttons
    buttons = page.locator(
        "button, [role='button'], input[type='submit'], input[type='button'], input[type='reset']"
    ).all()
    elements["buttons"] = [
        b.inner_text()[:100].strip()
        for b in buttons
        if b.is_visible()
    ]

    # Links (same-origin + external, capped)
    link_els = page.locator("a[href]").all()
    links = []
    for a in link_els[:50]:
        href = a.get_attribute("href") or ""
        if href.startswith(("javascript:", "#", "mailto:", "tel:")):
            continue
        links.append(
            {
                "text": a.inner_text()[:80].strip(),
                "href": href,
            }
        )
    elements["links"] = links

    # Inputs / Textareas / Selects
    input_els = page.locator("input:not([type='hidden']), textarea, select").all()
    elements["inputs"] = [
        {
            "type": i.get_attribute("type") or "text",
            "name": i.get_attribute("name") or "",
            "id": i.get_attribute("id") or "",
            "placeholder": i.get_attribute("placeholder") or "",
            "aria_label": i.get_attribute("aria-label") or "",
        }
        for i in input_els
        if i.is_visible()
    ]

    # Forms
    form_els = page.locator("form").all()
    elements["forms"] = [
        {
            "action": f.get_attribute("action") or "",
            "method": (f.get_attribute("method") or "get").upper(),
            "id": f.get_attribute("id") or "",
        }
        for f in form_els
    ]

    # Headings (page structure)
    heading_els = page.locator("h1, h2, h3").all()
    elements["headings"] = [
        h.inner_text()[:100].strip()
        for h in heading_els
        if h.is_visible()
    ][:10]

    # ARIA landmarks (nav, main, aside, etc.)
    landmark_els = page.locator(
        "[role='navigation'], [role='main'], [role='banner'], [role='dialog'], nav, main, header, footer"
    ).all()
    elements["landmarks"] = list(
        {
            (el.get_attribute("role") or el.evaluate("e => e.tagName.toLowerCase()"))
            for el in landmark_els
            if el.is_visible()
        }
    )

    return elements


# ---------------------------------------------------------------------------
# Crawler
# ---------------------------------------------------------------------------


def explore(start_url: str, max_depth: int, max_pages: int) -> dict:
    """
    BFS crawl starting from start_url.
    Visits at most max_pages URLs, following same-origin links up to max_depth.
    Returns a site_map dict.
    """
    SNAPSHOTS_DIR.mkdir(exist_ok=True)

    visited: dict[str, dict] = {}
    queue: list[tuple[str, int]] = [(start_url, 0)]
    seen: set[str] = {start_url}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
        )
        context.set_default_navigation_timeout(NAV_TIMEOUT)

        while queue and len(visited) < max_pages:
            url, depth = queue.pop(0)
            page_info: dict = {
                "url": url,
                "depth": depth,
                "title": "",
                "status_code": None,
                "elements": {},
                "child_urls": [],
                "screenshot": "",
                "error": None,
            }

            page = context.new_page()
            try:
                response = page.goto(url, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
                if response:
                    page_info["status_code"] = response.status

                page_info["title"] = page.title()

                # Screenshot
                slug = url_to_slug(url)
                screenshot_path = SNAPSHOTS_DIR / f"explore_{slug}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                page_info["screenshot"] = str(screenshot_path)

                # Collect elements
                page_info["elements"] = collect_page_elements(page)

                # Discover child links for BFS
                child_urls = []
                for link in page_info["elements"].get("links", []):
                    href = link["href"]
                    full_url = urljoin(url, href)
                    # Normalise: drop fragment
                    full_url = full_url.split("#")[0]
                    if (
                        full_url
                        and same_origin(full_url, start_url)
                        and full_url not in seen
                        and depth < max_depth
                    ):
                        seen.add(full_url)
                        queue.append((full_url, depth + 1))
                        child_urls.append(full_url)

                page_info["child_urls"] = child_urls[:10]

            except Exception as exc:
                page_info["error"] = str(exc)
            finally:
                page.close()

            visited[url] = page_info
            status_str = f"[{page_info['status_code']}]" if page_info["status_code"] else ""
            error_str = f" ERROR: {page_info['error']}" if page_info["error"] else ""
            print(
                f"  [{len(visited):>3}/{max_pages}] depth={depth} "
                f"{status_str} {url} — \"{page_info['title']}\"{error_str}"
            )

        browser.close()

    return {
        "start_url": start_url,
        "total_pages": len(visited),
        "pages": list(visited.values()),
    }


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------


def print_summary(site_map: dict) -> None:
    """Print a structured summary the agent can read directly from the log."""
    print()
    print("---")
    print(f"total_pages:  {site_map['total_pages']}")
    print(f"site_map:     {SITE_MAP_FILE}")
    print(f"screenshots:  {SNAPSHOTS_DIR}/explore_*.png")
    print("---")
    print()
    print("Page inventory:")
    for page in site_map["pages"]:
        el = page.get("elements", {})
        status = f"[{page['status_code']}] " if page["status_code"] else ""
        print(f"  {status}{page['url']}")
        if page["title"]:
            print(f"    title:     \"{page['title']}\"")
        if el.get("headings"):
            print(f"    headings:  {el['headings']}")
        if el.get("buttons"):
            print(f"    buttons:   {el['buttons']}")
        if el.get("inputs"):
            inputs_summary = [
                f"{i['type']}({i['name'] or i['id'] or i['placeholder'] or '?'})"
                for i in el["inputs"]
            ]
            print(f"    inputs:    {inputs_summary}")
        if el.get("forms"):
            print(f"    forms:     {len(el['forms'])} form(s)")
        print(f"    links:     {len(el.get('links', []))} link(s)")
        if page.get("error"):
            print(f"    ERROR:     {page['error']}")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crawl a web app and produce a site_map.json for the agent."
    )
    parser.add_argument("url", help="Starting URL to crawl (e.g. https://example.com)")
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Maximum link-follow depth from the start URL (default: 2)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Maximum number of pages to visit (default: 20)",
    )
    args = parser.parse_args()

    print(f"AutonomousTester Explorer")
    print(f"  Target:    {args.url}")
    print(f"  Max depth: {args.depth}")
    print(f"  Max pages: {args.max_pages}")
    print()

    site_map = explore(args.url, args.depth, args.max_pages)

    with open(SITE_MAP_FILE, "w") as f:
        json.dump(site_map, f, indent=2)

    print_summary(site_map)


if __name__ == "__main__":
    main()
