#!/usr/bin/env python3
"""Build the static Motorhome website from JSON content."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
DOCS_DIR = ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
SOURCE_ASSETS_DIR = ROOT / "src-assets"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def money(value: int, rounded: bool = False) -> str:
    amount = int(round(value / 1000) * 1000) if rounded else int(value)
    return "${:,.0f}".format(amount)


def number(value: int | float) -> str:
    if isinstance(value, float) and value % 1:
        return "{:,.2f}".format(value)
    return "{:,}".format(int(value))


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def nav_html() -> str:
    return """
<nav class="top-nav">
  <a href="/">Home</a>
  <a href="/about/">About</a>
  <a href="/contact/">Contact</a>
</nav>
"""


def header_html(site: dict[str, Any]) -> str:
    return f"""
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="/" aria-label="{esc(site['name'])} home">
      <img src="/images/logo-australia.png" alt="{esc(site['name'])}" />
    </a>
    {nav_html()}
    <a class="header-cta" href="/contact/">Email us today</a>
  </div>
</header>
"""


def footer_html(site: dict[str, Any]) -> str:
    addr = site["address"]
    return f"""
<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <p class="footer-heading">{esc(site['name'])}</p>
      <p>Used motorhomes for sale in Brisbane with free delivery from our South Australia yard.</p>
    </div>
    <div>
      <p class="footer-heading">Contact</p>
      <p><a href="mailto:{esc(site['email'])}">{esc(site['email'])}</a></p>
      <p>{esc(addr['streetAddress'])}, {esc(addr['addressLocality'])} {esc(addr['addressRegion'])} {esc(addr['postalCode'])}</p>
    </div>
  </div>
</footer>
"""


def trust_badges_html() -> str:
    labels = ["Satisfaction guaranteed", "Free delivery", "12-month warranty"]
    items = "".join(f"<li>{esc(label)}</li>" for label in labels)
    return f'<ul class="trust-badges">{items}</ul>'


def reviews_html(reviews: list[dict[str, Any]], compact: bool = False) -> str:
    items = []
    for review in reviews:
        items.append(
            f"""
<li class="review-item">
  <img src="{esc(review['image'])}" alt="" loading="lazy" />
  <div>
    <p class="review-stars" aria-label="5 stars">★★★★★</p>
    <p class="review-quote">"{esc(review['quote'])}"</p>
    <p class="review-author">{esc(review['name'])}, {esc(review['location'])}</p>
  </div>
</li>
"""
        )
    wrapper_class = "reviews-list compact" if compact else "reviews-list"
    return f"""
<section class="section">
  <div class="container">
    <h2 class="section-title">Reviews</h2>
    <p class="section-subtitle">4.9 on Google{" · 5,500+ sold" if compact else ""}</p>
    <ul class="{wrapper_class}">
      {''.join(items)}
    </ul>
  </div>
</section>
"""


def faq_html(faq_items: list[dict[str, str]], title: str = "Questions") -> str:
    details = []
    for item in faq_items:
        details.append(
            f"""
<details>
  <summary>{esc(item['question'])}</summary>
  <p>{esc(item['answer'])}</p>
</details>
"""
        )
    return f"""
<section class="section">
  <div class="container faq">
    <h2 class="section-title">{esc(title)}</h2>
    {''.join(details)}
  </div>
</section>
"""


def listing_faqs(site_content: dict[str, Any], listing: dict[str, Any]) -> list[dict[str, str]]:
    faqs: list[dict[str, str]] = []
    for item in site_content["listingFaqTemplate"]:
        if item["question"] == "What licence do I need?":
            if listing["licence"] == "Car":
                answer = item["answerCar"].format(
                    gvmKg=listing["gvmKg"],
                    licence=listing["licence"],
                )
            else:
                answer = item["answerOther"].format(
                    gvmKg=listing["gvmKg"],
                    licence=listing["licence"],
                )
            faqs.append({"question": item["question"], "answer": answer})
        else:
            faqs.append({"question": item["question"], "answer": item["answer"]})
    return faqs


def enquiry_form_html(site: dict[str, Any], listing_title: str | None = None, compact: bool = False, form_id: str = "enquire") -> str:
    title = "Enquire about this motorhome" if listing_title else "Enquire about a motorhome"
    intro = (
        "Interested? Send us your details and we will be in touch shortly."
        if compact
        else "Hold a car licence? Email us today. Name, email and mobile are required - add a message with anything else you want us to know."
    )
    button = "Enquire Now" if compact else "Email us today"
    card_class = "enquiry-card enquiry-card-compact" if compact else "enquiry-card"
    return f"""
<form id="{esc(form_id)}" class="{card_class} js-enquiry-form" data-email="{esc(site['email'])}" data-listing-title="{esc(listing_title or '')}">
  <div>
    <h2>{esc(title)}</h2>
    <p>{esc(intro)}</p>
  </div>
  <label>Name<input required name="name" autocomplete="name" /></label>
  <label>Email<input required type="email" name="email" autocomplete="email" inputmode="email" /></label>
  <label>Mobile<input required type="tel" name="sms" autocomplete="tel" inputmode="tel" minlength="8" placeholder="04xx xxx xxx" /></label>
  <label>Message <span>(optional)</span><textarea name="message" rows="{2 if compact else 4}"></textarea></label>
  <button type="submit">{esc(button)}</button>
  <div class="form-trust">
    {trust_badges_html()}
  </div>
</form>
"""


def page_shell(
    title: str,
    description: str,
    body: str,
    site: dict[str, Any],
    path: str,
    extra_head: str = "",
    scripts: str = "",
) -> str:
    canonical = site["url"].rstrip("/") + path
    return f"""<!doctype html>
<html lang="en-AU">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <meta name="application-name" content="{esc(site['name'])}" />
  <meta name="author" content="{esc(site['legalName'])}" />
  <link rel="icon" href="/icon.svg" type="image/svg+xml" />
  <link rel="canonical" href="{esc(canonical)}" />
  <link rel="stylesheet" href="/assets/styles.css" />
  {extra_head}
</head>
<body>
  {header_html(site)}
  <main>{body}</main>
  {footer_html(site)}
  <script src="/assets/app.js" defer></script>
  {scripts}
</body>
</html>
"""


def inventory_card_html(item: dict[str, Any]) -> str:
    title = f"{item['year']} {item['brand']} {item['model']}"
    return f"""
<article class="inventory-card">
  <a href="/inventory/{esc(item['slug'])}/">
    <div class="inventory-image-wrap">
      <img src="{esc(item['image'])}" alt="{esc(title)}" loading="lazy" />
    </div>
    <div class="inventory-card-body">
      <p class="inventory-meta">{esc(item['year'])} {esc(item['brand'])}</p>
      <h3>{esc(item['model'])}</h3>
      <p class="inventory-price">{esc(money(item['price'], rounded=True))} <span>· {esc(number(item['kilometres']))} km</span></p>
    </div>
  </a>
</article>
"""


def listing_key_benefits(listing: dict[str, Any]) -> list[str]:
    return [
        f"Sleeps {listing['berths']}",
        f"Seats {listing['seatbelts']}",
        "Automatic",
        listing["fuel"],
        "Kitchen",
        "Bathroom",
        "Shower",
        "Toilet",
        "Air conditioning",
        "Fridge",
        "Awning",
        f"{listing['licence']} licence",
    ]


def copy_source_assets() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for source, target_name in [
        (SOURCE_ASSETS_DIR / "styles.css", "styles.css"),
        (SOURCE_ASSETS_DIR / "app.js", "app.js"),
    ]:
        shutil.copy2(source, ASSETS_DIR / target_name)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_home(site_content: dict[str, Any], inventory: list[dict[str, Any]], reviews: list[dict[str, Any]]) -> str:
    site = site_content["site"]
    cards = "".join(inventory_card_html(item) for item in inventory)
    brands = "".join(
        f"<li><p>{esc(brand['name'])}</p><span>{esc(brand['subtitle'])}</span></li>"
        for brand in site_content["brands"]
    )
    stats = " · ".join(esc(part) for part in site_content["stats"])
    faqs = site_content["homeFaqs"]
    auto_schema = {
        "@context": "https://schema.org",
        "@type": "AutoDealer",
        "name": site["name"],
        "legalName": site["legalName"],
        "url": site["url"],
        "email": site["email"],
        "description": "Used motorhomes for sale in Brisbane — Avida, Sunliner, Avan and KEA from our South Australia yard. Car licence layouts, free delivery to Brisbane, 12-month warranty. Email us today and we will be in touch shortly.",
        "address": {"@type": "PostalAddress", **site["address"]},
        "taxID": site["taxId"],
        "areaServed": site["areaServed"],
        "brand": [brand["name"] for brand in site_content["brands"]],
    }
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {"@type": "Answer", "text": faq["answer"]},
            }
            for faq in faqs
        ],
    }
    body = f"""
<section class="hero">
  <div class="hero-image-wrap">
    <img src="/images/hero-brisbane.jpg" alt="Used motorhomes in Brisbane" />
  </div>
  <div class="container hero-content">
    <h1>{esc(site['tagline'])}</h1>
    <p>{esc(site['heroIntro'])}</p>
    <a class="primary-btn" href="#catalogue">Browse Available Stock</a>
    <p class="hero-stats">{stats}</p>
  </div>
</section>
<section class="section brand-strip">
  <div class="container">
    <ul class="brand-list">{brands}</ul>
  </div>
</section>
<section id="catalogue" class="section">
  <div class="container">
    <h2 class="section-title">Browse the full catalogue</h2>
    <p class="section-subtitle">Search current motorhomes by model or stock number.</p>
    <form class="inventory-filters" onsubmit="return false;">
      <label>Search<input id="inventory-search" type="search" placeholder="Model or stock no." /></label>
      <label>Sort
        <select id="inventory-sort">
          <option value="newest">Newest first</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
          <option value="km">Lowest kilometres</option>
        </select>
      </label>
    </form>
    <p class="inventory-count" id="inventory-count">{len(inventory)} motorhomes</p>
    <div id="inventory-grid" class="inventory-grid">{cards}</div>
  </div>
</section>
{reviews_html(reviews)}
{faq_html(faqs, title="Questions")}
"""
    scripts = f"""
<script id="inventory-data" type="application/json">{json.dumps(inventory, separators=(",", ":"))}</script>
<script type="application/ld+json">{json.dumps(auto_schema, separators=(",", ":"))}</script>
<script type="application/ld+json">{json.dumps(faq_schema, separators=(",", ":"))}</script>
"""
    return page_shell(
        title="Used motorhomes for sale in Brisbane | Commercial Motorhomes",
        description="Used motorhomes for sale in Brisbane — Avida, Sunliner, Avan and KEA from our South Australia yard. Car licence layouts, free delivery to Brisbane, 12-month warranty. Email us today and we will be in touch shortly.",
        body=body,
        site=site,
        path="/",
        scripts=scripts,
    )


def build_about(site_content: dict[str, Any]) -> str:
    site = site_content["site"]
    about = site_content["about"]
    brands = "".join(
        f"<li><p>{esc(brand['name'])}</p><span>{esc(brand['subtitle'])}</span></li>"
        for brand in site_content["brands"]
    )
    paragraphs = "".join(f"<p>{esc(paragraph)}</p>" for paragraph in about["paragraphs"])
    body = f"""
<section class="section">
  <div class="container prose">
    <p class="eyebrow">{esc(about['eyebrow'])}</p>
    <h1>{esc(about['title'])}</h1>
    {paragraphs}
    <h2>{esc(about['whyChooseUsTitle'])}</h2>
    <p>{esc(about['whyChooseUsBody'])}</p>
  </div>
</section>
<section class="section brand-strip">
  <div class="container">
    <ul class="brand-list">{brands}</ul>
  </div>
</section>
"""
    return page_shell(
        title="About us · Commercial Motorhomes",
        description="Learn about Commercial Motorhomes in Brisbane and our South Australia yard. Used Avida, Sunliner, Avan and KEA stock with free delivery and 12-month warranty.",
        body=body,
        site=site,
        path="/about/",
    )


def build_contact(site_content: dict[str, Any]) -> str:
    site = site_content["site"]
    contact = site_content["contact"]
    body = f"""
<section class="section">
  <div class="container contact-grid">
    <div class="prose">
      <p class="eyebrow">{esc(contact['eyebrow'])}</p>
      <h1>{esc(contact['title'])}</h1>
      <p>{esc(contact['intro'])}</p>
      <div class="map-wrap">
        <iframe title="Map of South Australia motorhome yard region" src="{esc(contact['mapEmbedUrl'])}" loading="lazy"></iframe>
      </div>
    </div>
    <div id="enquire">
      {enquiry_form_html(site=site, listing_title=None, compact=False, form_id="contact-enquire")}
    </div>
  </div>
</section>
"""
    return page_shell(
        title="Email us about a used motorhome in Brisbane · Commercial Motorhomes",
        description="Email Australian Motor Homes Pty Ltd today about used motorhomes for sale in Brisbane. Free delivery, 12-month warranty, car licence layouts. We will be in touch shortly.",
        body=body,
        site=site,
        path="/contact/",
    )


def build_listing(site_content: dict[str, Any], reviews: list[dict[str, Any]], listing: dict[str, Any]) -> str:
    site = site_content["site"]
    list_title = f"{listing['year']} {listing['brand']} {listing['model']}"
    page_title = f"{list_title} motorhome for sale Brisbane · Commercial Motorhomes"
    description = listing["summary"]
    benefits = "".join(f"<li>{esc(item)}</li>" for item in listing_key_benefits(listing))
    feature_items = "".join(f"<li>{esc(item)}</li>" for item in listing["features"])
    description_blocks = "".join(f"<p>{esc(line)}</p>" for line in listing["description"])
    specs = "".join(
        f"<div><dt>{esc(spec['label'])}</dt><dd>{esc(spec['value'])}</dd></div>"
        for spec in listing["specs"]
    )
    thumbs = "".join(
        f'<button class="gallery-thumb{" is-active" if idx == 0 else ""}" data-index="{idx}" type="button"><img src="{esc(img)}" alt="" loading="lazy" /></button>'
        for idx, img in enumerate(listing["gallery"])
    )
    faqs = listing_faqs(site_content, listing)
    faq_details = "".join(
        f"<details><summary>{esc(item['question'])}</summary><p>{esc(item['answer'])}</p></details>"
        for item in faqs
    )
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in faqs
        ],
    }
    listing_json = {
        "title": list_title,
        "priceRounded": money(listing["price"], rounded=True),
        "gallery": listing["gallery"],
    }
    body = f"""
<article class="listing-page">
  <section class="section listing-hero-section">
    <div class="container listing-grid">
      <div class="listing-gallery js-gallery">
        <div class="listing-main-image-wrap">
          <button type="button" class="gallery-nav gallery-prev" data-direction="-1" aria-label="Previous photo">‹</button>
          <img class="listing-main-image" src="{esc(listing['gallery'][0])}" alt="{esc(list_title)}" />
          <button type="button" class="gallery-nav gallery-next" data-direction="1" aria-label="Next photo">›</button>
          <p class="gallery-counter">1 of {len(listing['gallery'])}</p>
        </div>
        <div class="listing-thumbs">{thumbs}</div>
      </div>
      <div class="listing-summary">
        <p class="eyebrow">Stock {esc(listing['stockNumber'])} · {esc(number(listing['kilometres']))} km</p>
        <h1>{esc(list_title)}</h1>
        <p class="listing-price">{esc(money(listing['price'], rounded=True))}</p>
        <p class="listing-summary-copy">{esc(listing['summary'])}</p>
        <h2 class="mini-title">Key benefits</h2>
        <ul class="benefits">{benefits}</ul>
      </div>
    </div>
  </section>
  <section class="section">
    <div class="container prose listing-content">
      {description_blocks}
      <h2>Features</h2>
      <ul>{feature_items}</ul>
      <h2>Specifications</h2>
      <dl class="spec-grid">{specs}</dl>
    </div>
  </section>
  <section id="enquire" class="section">
    <div class="container">
      {enquiry_form_html(site=site, listing_title=list_title, compact=True, form_id=f"listing-enquire-{listing['slug']}")}
    </div>
  </section>
  {reviews_html(reviews, compact=True)}
  <section class="section">
    <div class="container faq">
      <h2 class="section-title">Frequently asked questions</h2>
      {faq_details}
    </div>
  </section>
</article>
<div class="mobile-cta js-mobile-cta">
  <div>
    <p>{esc(list_title)}</p>
    <strong>{esc(money(listing['price'], rounded=True))}</strong>
  </div>
  <a href="#enquire">Enquire</a>
</div>
"""
    scripts = f"""
<script id="listing-data" type="application/json">{json.dumps(listing_json, separators=(",", ":"))}</script>
<script type="application/ld+json">{json.dumps(faq_schema, separators=(",", ":"))}</script>
"""
    return page_shell(
        title=page_title,
        description=description,
        body=body,
        site=site,
        path=f"/inventory/{listing['slug']}/",
        scripts=scripts,
    )


def ensure_clean_docs() -> None:
    for path in [DOCS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    for subdir in ["about", "contact", "inventory"]:
        target = DOCS_DIR / subdir
        if target.exists():
            shutil.rmtree(target)


def main() -> None:
    site_content = load_json(CONTENT_DIR / "site.json")
    inventory = load_json(CONTENT_DIR / "inventory.json")
    reviews = load_json(CONTENT_DIR / "reviews.json")

    ensure_clean_docs()
    copy_source_assets()

    write_file(DOCS_DIR / "index.html", build_home(site_content, inventory, reviews))
    write_file(DOCS_DIR / "about" / "index.html", build_about(site_content))
    write_file(DOCS_DIR / "contact" / "index.html", build_contact(site_content))

    for listing in inventory:
        path = DOCS_DIR / "inventory" / listing["slug"] / "index.html"
        write_file(path, build_listing(site_content, reviews, listing))

    print(f"Built {len(inventory) + 3} pages into {DOCS_DIR}")


if __name__ == "__main__":
    main()
