# TERRACOTTA – Content & SEO Implementation Notes

Phase: content, product data and SEO only. No images, CSS, layout or behaviour were changed.

## How the site is built

- `site/templates/home.html` – English homepage source. Its head, header, mega menu, pre-footer and footer are the shell of every page.
- `site/data/products.json` – categories, products, colours, SEO titles, URLs.
- `site/data/i18n.json` – translations (keys are the English strings), `active` languages, markets and hreflang codes.
- `site/tools/build_pages.py` – builds every page in every active language. Run `python3 site/tools/build_pages.py` after any change.
  If a translation is missing, the build lists it in `site/data/i18n-missing.json`.
- Output: `/en/`, `/de/`, `/fr/` (one folder per language), root `index.html` (sends visitors to their browser language, otherwise `/en/`), `sitemap.xml` (with hreflang), `robots.txt`.

## Language architecture

| Language | URL | hreflang | Priority | Status |
|---|---|---|---|---|
| English | /en/ | en, en-US, en-GB, en-AU, en-CA | P1 | Live |
| German | /de/ | de, de-DE | P1 | Live, all pages translated |
| French | /fr/ | fr, fr-FR, fr-CA | P1 | Live, all pages translated |
| Dutch | /nl/ | nl, nl-NL | P2 | Prepared in `markets`; needs translations, then add `nl` to `active` |
| Korean | /ko/ | ko, ko-KR | P2 | Prepared in `markets`; needs translations, then add `ko` to `active` |
| Arabic | /ar/ | ar, ar-AE | P2 | Needs a separate right-to-left (RTL) development phase |
| Spanish, Russian | – | – | – | Not in the architecture; translations kept in `i18n.json`, pages not built |

URL slugs stay in English in every language (e.g. `/de/products/terracotta-pavers/`). Page titles, H1s and descriptions carry the local keywords.

## Keywords used

| Language | Used in titles / H1 / descriptions |
|---|---|
| English | Terracotta Tiles. "Handmade Terracotta Tiles" is not used until handmade production is verified. |
| German | Terrakotta Fliesen, Terracotta Bodenfliesen, Cotto |
| French | Carrelage terre cuite, Carreaux en terre cuite, Tomettes |

Search volume and intent should be validated with Keyword Planner.

## Component mapping

| Existing component | New content |
|---|---|
| TILES mega menu – left image cards | Product Catalogue, Colour Collection, Custom Artisan Tiles |
| TILES mega menu – six columns | Six categories, two product links each |
| Mobile menu – collapsible groups | Same six categories and twelve products |
| "Explore the Collection" carousel | Twelve product cards (five reuse images already on the page) |
| Squares carousel | Six category cards |
| Text + media blocks | Brand intro, decorative tiles, surface & finish, wall, steps, outdoor |
| Environments carousel | Room types linked to relevant categories |
| Projects block | Residential / Hospitality / Outdoor Living, linked to /projects/ |
| Magazine block | Three planned article topics, linked to /magazine/ |
| Pre-footer (Design Your Space) | Categories, Colours, More Colours, Featured |
| Generic page template (no-image header + text blocks + CTA banner) | All new pages |
| `.ae-form` styles | Contacts and Request a Quote forms |

## Pages (per language)

Homepage, Product Catalogue, Colour Collection, Custom Artisan Tiles, 6 category pages, 12 product pages, Company, Projects, Magazine, Awards, Contacts, Request a Quote, Technical Information, Materials & Craft, Installation & Care, and 6 legal placeholders (noindex). 37 pages × 3 languages.

## Domain

`https://terracottaceramictiles.com` (set as `siteUrl` in `products.json`). Used for canonicals, hreflang, structured data, sitemap and site search.

## Open items

| Item | Status |
|---|---|
| Forms | Connected to Formspree (form ID `xgakokqp`) with @formspree/ajax 1.1.5, self-hosted in `site/assets/js/`. File uploads depend on the Formspree plan. |
| Product data | Colours per product, dimensions, surface & finish and specifications are `null` and shown as "to be confirmed". |
| Legal pages | Placeholder text only. Real legal texts are needed before launch. |
| Search | Uses Google site search for terracottaceramictiles.com; works once the site is indexed. |
| Translations | See language architecture above. Colour names stay in English. Form option values are submitted in English; a hidden `language` field tells which language the visitor used. |
| Projects, Awards, Magazine | No verified projects, awards or articles yet. |
| Breadcrumbs | Structured data only; the design has no visible breadcrumb component. |
| Favicon | The former favicon was removed; a TERRACOTTA favicon has not been created yet. |

## Former brand traces removed

Asset folders and logo files renamed, favicons, verification tags, award overlays, effect stamps, video links to the former brand's YouTube channel, the slogan image ("MATTER ABOVE ALL" replaced by "THE ART OF EARTH"), and images showing the former brand's name, technology names or factory were removed or swapped for other images already on the site.

## Still to replace in the visual phase

| Asset | Reason |
|---|---|
| Hero video | Former brand campaign footage |
| All product, room, project and article photos | Former brand's porcelain products and real projects |
