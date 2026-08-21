# Motorhome website rebuild

This repository is a full static rebuild of the public Motorhome site at:

- https://moonhus.github.io/motorhome/

It recreates:

- Home page
- About page
- Contact page
- All current in-stock vehicle detail pages
- Search/sort catalogue behavior
- Enquiry mailto forms

The site is generated from structured JSON content so handover is simple.

## Project structure

- `content/site.json` - global site copy, business metadata, FAQ templates
- `content/inventory.json` - full vehicle stock records (20 listings)
- `content/reviews.json` - customer review entries
- `scripts/sync_assets.py` - downloads all listing/review/brand images locally
- `scripts/build_site.py` - builds static pages into `docs/`
- `src-assets/styles.css` - shared styling source
- `src-assets/app.js` - shared browser behavior
- `docs/` - generated, deployable static site output

## Rebuild workflow (handover-friendly)

1. Update content:
   - Edit `content/inventory.json` for stock changes
   - Edit `content/reviews.json` for testimonial changes
   - Edit `content/site.json` for global copy, contact details, FAQs, canonical URL
2. (Optional) re-pull media assets from the live site:
   - `python3 scripts/sync_assets.py`
3. Regenerate all pages:
   - `python3 scripts/build_site.py`
4. Preview locally:
   - `python3 -m http.server --directory docs 4173`
   - open `http://localhost:4173`

## Notes

- The current canonical URL in generated pages is `https://moonhus.github.io/motorhome`.
  Update `content/site.json` (`site.url`) before deploying to a new domain.
- The contact flow is intentionally mailto-based to match the original behavior.
- `docs/` is ready for static hosting (including GitHub Pages).
