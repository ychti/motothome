#!/usr/bin/env python3
"""Mirror the live Motorhome site into docs/ with project-site base path."""

from __future__ import annotations

import json
import re
import shutil
from collections import deque
from pathlib import Path
from urllib.parse import urljoin

import requests


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
CONTENT_DIR = ROOT / "content"
SOURCE_BASE = "https://moonhus.github.io"
SOURCE_PREFIX = "/motorhome"
TARGET_PREFIX = "/motothome"


TEXT_TYPES = (
    "text/",
    "application/javascript",
    "application/json",
    "application/xml",
    "image/svg+xml",
)


def load_inventory_slugs() -> list[str]:
    inventory_path = CONTENT_DIR / "inventory.json"
    items = json.loads(inventory_path.read_text(encoding="utf-8"))
    return [item["slug"] for item in items]


def rewrite_base_paths(text: str) -> str:
    # Rewrite all absolute site-root refs from /motorhome to /motothome.
    text = text.replace("https://moonhus.github.io/motorhome", "https://ychti.github.io/motothome")
    text = text.replace("/motorhome/", "/motothome/")
    # Catch edge where path ends exactly at "/motorhome"
    text = re.sub(r'(?<=[\'"(=])\/motorhome(?=[\'")?&#\s])', "/motothome", text)
    return text


def extract_motorhome_paths(text: str) -> set[str]:
    paths = set(re.findall(r"/motorhome/[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]*", text))
    cleaned = set()
    for path in paths:
        # strip trailing punctuation that can appear in CSS/JS contexts
        trimmed = path.rstrip('"\'),;')
        if trimmed:
            cleaned.add(trimmed)
    return cleaned


def docs_path_from_source_path(source_path: str) -> Path:
    rel = source_path.removeprefix("/motorhome/")
    if source_path == "/motorhome":
        rel = ""
    return DOCS_DIR / rel


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def save_binary(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def is_text_content(content_type: str) -> bool:
    return any(content_type.startswith(prefix) for prefix in TEXT_TYPES)


def route_to_output(route: str) -> Path:
    if route in ("", "/"):
        return DOCS_DIR / "index.html"
    clean = route.strip("/")
    return DOCS_DIR / clean / "index.html"


def fetch_text(url: str) -> str:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def mirror_routes(queue: deque[str], seen_assets: set[str]) -> None:
    while queue:
        route = queue.popleft()
        source_url = urljoin(SOURCE_BASE, f"{SOURCE_PREFIX}/{route}")
        html = fetch_text(source_url)
        rewritten = rewrite_base_paths(html)
        save_text(route_to_output(route), rewritten)

        for path in extract_motorhome_paths(html):
            if path.startswith("/motorhome/_next/") or path.startswith("/motorhome/images/") or path.startswith("/motorhome/icon"):
                seen_assets.add(path)


def mirror_assets(initial_assets: set[str]) -> None:
    queue = deque(sorted(initial_assets))
    seen: set[str] = set()

    while queue:
        source_path = queue.popleft()
        if source_path in seen:
            continue
        seen.add(source_path)

        source_url = urljoin(SOURCE_BASE, source_path)
        response = requests.get(source_url, timeout=90)
        if response.status_code != 200:
            print(f"WARN {response.status_code}: {source_url}")
            continue

        output_path = docs_path_from_source_path(source_path)
        if source_path.endswith("/"):
            output_path = output_path / "index.html"

        content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
        if is_text_content(content_type):
            text = response.text
            rewritten = rewrite_base_paths(text)
            save_text(output_path, rewritten)
            for discovered in extract_motorhome_paths(text):
                if discovered not in seen:
                    queue.append(discovered)
        else:
            save_binary(output_path, response.content)


def main() -> None:
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    slugs = load_inventory_slugs()
    routes = ["", "about/", "contact/"] + [f"inventory/{slug}/" for slug in slugs]
    route_queue = deque(routes)
    asset_paths: set[str] = set()

    mirror_routes(route_queue, asset_paths)
    mirror_assets(asset_paths)

    print(f"Mirrored {len(routes)} pages and {len(asset_paths)} initial assets into {DOCS_DIR}")


if __name__ == "__main__":
    main()
