#!/usr/bin/env python3
"""Download all live Motorhome image assets for local hosting."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin

import requests


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
CONTENT_DIR = ROOT / "content"
BASE_URL = "https://moonhus.github.io/motorhome/"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def collect_paths() -> list[str]:
    inventory = load_json(CONTENT_DIR / "inventory.json")
    reviews = load_json(CONTENT_DIR / "reviews.json")

    paths: set[str] = {
        "/images/logo-australia.png",
        "/images/hero-brisbane.jpg",
        "/icon.svg",
    }

    for item in inventory:
        if item.get("image"):
            paths.add(item["image"])
        for image in item.get("gallery", []):
            paths.add(image)

    for review in reviews:
        if review.get("image"):
            paths.add(review["image"])

    return sorted(paths)


def download(path: str) -> bool:
    destination = DOCS_DIR / path.lstrip("/")
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = urljoin(BASE_URL, path.lstrip("/"))
    response = requests.get(url, timeout=45)
    if response.status_code != 200:
        print(f"FAILED {response.status_code}: {url}")
        return False
    destination.write_bytes(response.content)
    return True


def main() -> None:
    paths = collect_paths()
    ok = 0
    failed = 0
    for path in paths:
        if download(path):
            ok += 1
        else:
            failed += 1
    print(f"Downloaded {ok} assets to {DOCS_DIR}")
    if failed:
        print(f"{failed} assets failed to download")


if __name__ == "__main__":
    main()
