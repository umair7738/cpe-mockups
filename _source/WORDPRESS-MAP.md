# WordPress map: machine listings

How the mockup's listing pages (`/sales/used/`, `/sales/sold/`, `/rental/{main}/{sub}/`, `/rental/`) and rental main-category pages (`/rental/{main}/`, section 8) map to the custom theme.
Each mockup part has one WordPress equivalent. Build the PHP from the mockup output, and the existing CSS and JS keep working.

| Mockup | WordPress |
|---|---|
| `_source/data/machines.json` | `machine` posts, taxonomies and ACF fields |
| Template-part functions in `_source/build.py` | `template-parts/*.php` |
| `window.CPE` inline config | `wp_localize_script('cpe-listing', 'CPE', …)` |
| `assets/js/listing.js` | `wp_enqueue_script('cpe-listing', …)`. Only `renderResults()` changes |
| `assets/css/style.css` | `wp_enqueue_style(…)`, unchanged |

---

## 1. Data: post type, taxonomies, ACF

`machines.json` holds one object per machine (258 in total: 30 rental, 16 used, 212 sold). Each object looks like a WP post:

```json
{ "id": 101, "title": "2018 JLG E450AJ", "slug": "2018-jlg-e450aj",
  "taxonomies": { "machine_type": "articulated-boom-lifts", "machine_brand": "jlg", "listing_status": "used" },
  "acf": { "model": "JLG E450AJ", "year": 2018, "working_height": 15.7, … } }
```

- **Post type:** `machine`
- **`id`, `title`, `slug`:** post ID, `post_title`, `post_name`. The mockup IDs are grouped (rental 1+, used 101+, sold 1001+); WordPress will assign its own.
- **`null`:** the field isn't recorded yet. Leave the ACF field empty.
- **`_comment*` keys:** notes for the content team. They aren't content, so don't import them.

### Taxonomies
| Taxonomy | Terms (slug → name) |
|---|---|
| `machine_type` (**hierarchical**) | Parent `boom-lifts` Boom Lifts → `telescopic-boom-lifts` Telescopic Boom Lift · `articulated-boom-lifts` Articulated Boom Lift · `electric-boom-lifts` Electric Boom Lift<br>Parent `scissor-lifts` Scissor Lifts → `slab-electric-scissor-lifts` Slab Electric Scissor Lift · `rough-terrain-electric-scissor-lifts` Rough Terrain Electric Scissor Lift · `diesel-4x4-scissor-lifts` Diesel 4x4 Scissor Lift<br>Parent `spider-lifts` Spider Lifts (no children yet; term meta `status` = `coming-soon`, `height_range` = `17 – 36 m`)<br>Machines are assigned the **child** term only. The old terms `electric-scissor-lifts` and `rough-terrain-scissor-lifts` no longer exist (see section 8). |
| `machine_brand` | `jlg` JLG · `genie` Genie · `dingli` Dingli · `snorkel` Snorkel |
| `listing_status` | `rental` · `used` · `new` · `sold` |

### ACF fields
| Field | Type | Used by | Notes |
|---|---|---|---|
| `model` | text | all | e.g. "JLG E450AJ" (brand included). Search matches it. |
| `year` | number | used, sold | model year |
| `working_height` | number (m) | rental, used | |
| `platform_height` | number (m) | rental (scissors) | |
| `capacity` | number (kg) | rental | |
| `outreach` | number (m) | rental (booms) | |
| `weight` | number (kg) | rental | machine weight. Not in the original field list, but the spec tables and detail pages show it. |
| `width` | number (m) | (none yet) | all empty |
| `hours` | text | used | 4 sample values for the home page, marked by `_comment_hours`. Replace them with real hour-meter readings. |
| `power` | text | rental | "Electric" / "Diesel" |
| `origin` | text | used, sold | country name |
| `sold_to` | text | sold | country name; empty = not recorded |
| `sold_date` | text `YYYY-MM` | sold | `YYYY-00` = month unknown; empty = not recorded |
| `availability` | select | rental | `available` / `on-hire` |
| `return_date` | date | (none yet) | all empty (for "on hire until …") |
| `stock_no` | text | used, sold | **Needed for sales URLs** (last part of `/sales/{year}-{brand}-{model}-{stock id}/`), e.g. `CP1001`. All empty in the mockup, so the build uses the placeholder `cp{post ID}`. Not shown on the page (business decision). |
| `photo_count` | number | (none yet) | all empty |
| `image` | image | all | Mockup: an image basename in `assets/img/` (the `-sm` variant is used on cards). For sold records this is a photo of the **model**, not the unit. |

### Permalinks (custom rewrite rules)
- Rental machine: `/rental/{slug}/` (flat; the category is shown only in the breadcrumbs, so re-categorising a machine never changes its URL)
- Rental main category: `/rental/{parent term}/`; sub-category: `/rental/{parent term}/{child term}/`
- `/rental/{x}/` is resolved **term first**: if `x` is a `machine_type` parent term (or `all-machines`), show that page; otherwise look up a rental `machine` post with slug `x`. A machine slug must never equal a parent term slug – `build.py` asserts this for the mockup data.
- Sales machine (used, new, sold): `/sales/{year}-{brand}-{model}-{stock id}/`, e.g. `/sales/2010-jlg-600aj-cp1001/`
  - Built from ACF `year`, the `machine_brand` term, ACF `model` (brand prefix dropped) and ACF `stock_no`, all lower-case with `-` (`sanitize_title`). Set it as the post's `post_name` on save.
  - No status in the URL: when a used machine sells, only its `listing_status` changes and the URL stays the same – no redirect, and the page keeps its search ranking. The status shows in the breadcrumbs (Sales › Used Equipment / Sold Equipment).
  - `/sales/{x}/` is resolved **listing page first**: `new`, `used` and `sold` are the listing pages; anything else is a sales `machine` post. A sales slug always starts with the year, so it can never clash.

### Slugs must be unique
The stock ID makes every sales URL unique, including the same model and year sold more than once (e.g. three 2010 JLG 600AJ: `-cp112`, `-cp1038`, `-cp1194`). `build.py` asserts that no two machines share a URL. Every used and sold machine therefore needs a `stock_no` before import; WordPress would otherwise add `-2` to a duplicate.

---

## 2. Template parts

Each part is one function in `build.py`, with a comment above it naming the PHP file. The page functions in `build.py` only assemble these parts.

| build.py | PHP file | Args (`$args` / mockup `ctx`) |
|---|---|---|
| `machine_card(item, variant)` | `template-parts/machine-card.php` | `variant`: `rental` \| `used` \| `sold` (defaults to `listing_status`) |
| `listing_toolbar(ctx)` | `template-parts/listing-toolbar.php` | `search` (placeholder text, or empty = no search box), `sorts` |
| `listing_filters(ctx)` | `template-parts/listing-filters.php` | `groups` (title, param, options with counts), `total`, `nouns`, `label` |
| `listing_empty(ctx)` | `template-parts/listing-empty.php` | `page_type`, `search`, `tries` + the copy in `EMPTY_COPY` |
| `listing_pagination(ctx)` | `template-parts/pagination.php` | `total`, `per_page`, `paged` + the current query string |
| `listing_results(ctx)` / `listing(ctx)` | `archive-machine.php` (or a page template) | assembles the parts above |

### Markup rules for the PHP
Keep these classes and attributes:
- **Results region:** `<div id="cpe-results" data-total data-paged>`. It holds:
  - `[data-cpe-heading]`, the count heading ("Showing 25–48 of 212 records"; "Showing 16 machines" when everything fits on one page)
  - `[data-cpe-grid]`, the cards
  - `[data-cpe-empty]`, the no-results block
  - `[data-cpe-pager]`, the pagination
- **Outside the results region**, never swapped:
  - the filter form `form#cpe-filters[data-cpe-filters]` (checkboxes `name="m_…"`, submit `[data-cpe-filter-apply]`, `[data-cpe-clear-all]`)
  - the toolbar (`[data-cpe-search]`, `[data-cpe-search-clear]`, `[data-cpe-sort]`, `[data-cpe-filter-open]`)
  - the chips `[data-cpe-chips]`
  - the live region `[data-cpe-announce]`
- **Cards:** `[data-cpe-item]` plus the `data-*` attributes named after the fields. The mockup JS filters on them. In WordPress they're optional, because the server filters.
- **Pagination:** real links `?{current params}&paged=N`. Page 1 drops `paged`. Nothing is rendered when there are 24 results or fewer.
  - Desktop shows `‹ Previous 1 … 4 5 6 … 9 Next ›`; ≤768px shows `‹ Page 5 of 9 ›`. The CSS switches between them, so output both parts.
  - The page-list rule (current ±1, first, last; a gap of one page shows that page) is in `page_list()`.
- **No-results block:**
  - Heading for each page type:
    - used: "No {term} in stock right now"
    - sold: "No sold records for {term}"
    - rental: "No {term} in our rental fleet right now"
    - with no search term: "No machines/records match these filters"
  - "Tell us your spec" → `/contact/?machine={term}&need=buy|rent#enquiry`
  - WhatsApp → `https://wa.me/971561018428?text=` followed by the encoded text from `EMPTY_COPY`
  - "Clear filters" only when filters are active
  - "Try:" chips (`[data-cpe-try]`)

---

## 3. URL parameters

These avoid the reserved WP query vars (`page`, `year`, `type`, `s`, `search`, …). Register them with the `query_vars` filter.

| Param | Value format | Field | WP query |
|---|---|---|---|
| `q` | text | `model`, brand, `origin`, `sold_to`, "year model" | custom search (see "Search rules" below). Don't use `s`. |
| `m_type` | comma-separated term slugs | `machine_type` | `tax_query` IN |
| `m_brand` | comma-separated term slugs | `machine_brand` | `tax_query` IN |
| `m_year` | comma-separated ranges | `year` | `meta_query` NUMERIC, OR across the ranges |
| `m_height` | comma-separated ranges | `working_height` | same |
| `m_capacity` | comma-separated ranges | `capacity` | same (rental) |
| `m_outreach` | comma-separated ranges | `outreach` | same (rental) |
| `m_origin` | comma-separated slugs of the text | `origin` | `meta_query`; compare against `sanitize_title(value)` |
| `m_sold_to` | comma-separated slugs, `not-recorded` = empty | `sold_to` | same; `not-recorded` → `NOT EXISTS` / empty |
| `m_sold_year` | comma-separated years, `not-recorded` = empty | `sold_date` | `LIKE 'YYYY-%'` |
| `m_availability` | `available`, `on-hire` | `availability` | `meta_query` IN |
| `m_sort` | `field-dir`, e.g. `year-desc`, `working_height-asc`, `sold_date-desc`, `capacity-desc` | that field | `orderby=meta_value_num`, `order`. The first option of the select is the default and isn't written to the URL. Turn `sold_date` into a number before sorting (`YYYYMM`; empty = 0). |
| `paged` | integer | | native paging; 24 per page |

**Range format:** `min-max`. Min is inclusive and max is exclusive; either end may be empty.
- `-20` = below 20
- `20-30` = 20 up to (not including) 30
- `30-` = 30 and above

These are the checkbox values, and the home-page finder sends free ranges too (e.g. `m_height=12-20`).

**Logic:** OR inside a group, AND across groups, and AND with `q`.

**Two input forms (both must work):**
- JS writes comma lists: `?m_type=a,b`.
- A form submitted without JS sends repeated keys: `?m_type=a&m_type=b`. PHP's `$_GET` keeps only the last of repeated keys, so parse `$_SERVER['QUERY_STRING']` yourself:

```php
function cpe_param_list( $key ) {
    $out = [];
    foreach ( explode( '&', $_SERVER['QUERY_STRING'] ?? '' ) as $pair ) {
        [ $k, $v ] = array_pad( explode( '=', $pair, 2 ), 2, '' );
        if ( urldecode( $k ) !== $key ) continue;
        foreach ( explode( ',', urldecode( $v ) ) as $x ) { $x = sanitize_text_field( trim( $x ) ); if ( $x !== '' ) $out[] = $x; }
    }
    return array_values( array_unique( $out ) );
}
```

**Out-of-range `paged`:** WordPress returns a 404 by default. The mockup clamps to the last page (`?q=860sj&paged=9` shows the last page of the 860SJ results), so match that, e.g. with a `template_redirect` that redirects to the last page.

### Search rules (`q`)
- Ignore case, spaces, `-`, `#` and `.`, so "e 450", "E-450" and "e450" all find "JLG E450AJ".
- Match the whole normalised query as a substring of any field first.
- Only if nothing matches **and** the query has more than one word, every word must match some field ("860sj denmark"). This keeps "e 450" from matching "M450AJ" through the separate words "e" and "450".
- The reference implementation is `searchHits()` in `listing.js`.

---

## 4. `window.CPE` → `wp_localize_script`

`build.py` prints it once in `<head>`, on listing pages only:

```js
window.CPE = { "whatsapp": "971561018428", "pageType": "used", "perPage": 24, "nouns": ["machine", "machines"], "search": true };
```

| Key | Meaning |
|---|---|
| `whatsapp` | number for wa.me links |
| `pageType` | `used` \| `sold` \| `rental` (GA4 `page_type`, empty-state copy) |
| `perPage` | 24 |
| `nouns` | singular / plural for counts ("record", "records" on the sold page) |
| `search` | whether the page has the search box. To turn search off for a page, leave out the search markup. In the mockup that's `search=None` in `listing_ctx()`, or `CATS[...]["search"] = False` for a rental category. |

---

## 5. JavaScript: what changes in WordPress

**Only `renderResults(state)` in `assets/js/listing.js`.** The comment above it has the replacement: fetch `buildUrl(state)`, parse the HTML, swap `#cpe-results`, and resolve `{ total, paged }` from its `data-total` / `data-paged`.

Everything else stays the same:
- URL building and reading (`readParams`, `buildQuery`, `buildUrl`)
- history: `pushState` for pages, checkboxes, sort, chips and clear buttons; `replaceState` while typing; `popstate`
- 200 ms search debounce, Enter/Esc, the × button, Clear all (filters + search) and Clear filters (filters only)
- "Try:" chips, active-filter chips, the mobile drawer
- focus: only pagination moves focus (to the results heading, after scrolling to the top of `#cpe-results`). Search and filter changes announce "12 machines found" in `[data-cpe-announce]`.
- GA4 push after each debounced search of 2+ characters, and once for `?q=` on page load. The same term isn't pushed twice in a row:
  `dataLayer.push({ event: 'search_listing', page_type, search_term, results_count, search_source: 'typed'|'url' })`
- the `seq` guard in `update()`, which drops out-of-order fetch responses

### Required: facet counts with the results
The sidebar shows a count next to every filter option. Each count is computed against **the current search plus all the other filter groups** (not its own group).

The mockup recomputes these on every change (`renderFacetCounts()`). **The WordPress response must return the counts with the results.** Simplest approach: `listing-filters.php` renders the counts for the current request, and after the fetch `renderResults()` copies each `.count` (and the `is-zero` class) from the fetched `#cpe-filters` into the live form. Don't replace the form itself, because that would reset focus.

---

## 6. Mockup-only parts (don't port)
- All cards are output, with the ones beyond page 1 marked `hidden`, and the JS paginates them. WordPress renders only the current page.
- `CPE_PAGE` / `listing()` setting the config while a page renders: that's just how the static builder places `window.CPE`.
- `{{card:status:slug}}`, `{{hrcard:…}}`, `{{hscard:…}}` tokens in `_source/pages/*.html`: the hand-written partials' way to include machine cards.

## 7. Quote popup and quote forms

Files: `assets/partials/quote-modal.html` (popup markup, generated from `_source/quote.py`), `assets/css/quote-modal.css`, `assets/js/quote-modal.js`. No libraries.

**Setup in WordPress**
- Enqueue `quote-modal.css` and `quote-modal.js` (`defer`) on every page.
- Put the `<dialog id="quote-modal">` markup once, just before `</body>`: `footer.php`, or an Elementor HTML widget in the site-wide footer template. Leave it out on the Contact page, where the quote buttons scroll to the inline form instead.
- Set `QUOTE_CONFIG.endpoint` at the top of `quote-modal.js` to the form handler URL: an `admin-ajax.php` / REST route, or a form plugin endpoint. It receives a `FormData` POST and must return HTTP 2xx on success. With `endpoint: null` the forms run in mockup mode and send nothing.

**Buttons (template parts):** keep a real link to `/contact/#enquiry` (it is the no-JS fallback) and add the data attributes:

| Button | Attributes |
|---|---|
| Header / mobile bar / generic | `data-quote` |
| Rental card / rental detail | `data-quote data-type="rental" data-machine="{model}" data-category="{child machine_type singular, e.g. Slab electric scissor lift}"` |
| Boom / Scissor main-category page | `data-quote data-type="rental"` (no category – the visitor picks the type) |
| Used card / sale detail | `data-quote data-type="sale" data-machine="{year} {model}"` |
| Sold card / sold detail | `data-quote data-type="sale" data-machine="{model}" data-sold` |
| Service buttons | `data-quote data-type="service"` |
| Spider lift (coming soon) | `data-quote data-type="rental" data-category="Spider lift (coming soon)"` |

**Inline forms:** any `<form data-quote-form="inline" novalidate>` gets the same validation, success message and tracking. The shared field set (home, Contact, detail sidebars) is `quote_fields()` in `_source/quote.py`. Field groups carry `data-for="rental|sale|service"`, and the JS hides and disables the groups that don't match the chosen type.

**Fields sent:** `enquiry_type` (rental/sale/service), `name`, `phone`, `company`, `email`, `machine` (specific model, hidden), `machine_category`, `machine_model`, `service_needed`, `service_machine`, `emirate`, `country`, `start_date`, `rental_period`, `operator`, `details`, `page_url`, `page_title`, and ad attribution (`gclid`, `gbraid`, `wbraid`, `utm_*`, from `sessionStorage`). Each type only sends its own fields. `website` is a honeypot: the handler should drop any enquiry where it is filled (the JS already shows a fake success and sends nothing).

**Tracking (GTM `dataLayer`):** `generate_lead` {form_id: `quote_popup` | `inline_enquiry`, enquiry_type, machine} on success; `whatsapp_click` {location: `quote_popup`, machine} from the popup's WhatsApp buttons.

**Links from ads:** `#quote` on any URL opens the popup (`#enquiry` too, on pages without an `#enquiry` section). `?machine=`, `?type=rental|sale|service` (or `?need=rent|buy`) and `?category=` pre-fill it.

**Quote categories** (`CATEGORIES` in `_source/quote.py`; the popup's "Machine needed" options and the values `data-category` must match): Telescopic boom lift · Articulated boom lift · Electric boom lift · Slab electric scissor lift · Rough terrain electric scissor lift · Diesel 4x4 scissor lift · Spider lift (coming soon). Spider stays last.

## 8. Rental main and sub-categories, redirects and SEO

### Pages
| Mockup (`build.py`) | URL | WordPress |
|---|---|---|
| `page_rental_landing()` | `/rental/` | page template; 3 cards, one per parent term (`group_tile()`) |
| `page_rental_group(g)` | `/rental/boom-lifts/`, `/rental/scissor-lifts/`, `/rental/spider-lifts/` | `taxonomy-machine_type.php` when the queried term has no parent: hero + intro (term description / ACF), one `template-parts/category-card.php` per child term (`cat_tile()`), compare table computed from the child terms' machines, "how to choose", rental options, FAQ, related links |
| `page_rental_group(g)` with `soon` | `/rental/spider-lifts/` | same template; when term meta `status` = `coming-soon`, show the coming-soon panel and "Register interest" (`data-category="Spider lift (coming soon)"`) instead of the cards and table |
| `page_rental_category(c)` | `/rental/{parent}/{child}/` | `taxonomy-machine_type.php` for a child term: the existing listing (section 2). The chip row lists the sibling child terms + "← All {parent}" |
| `nav_tree()`, `menu_html()` | header (every page) | Main menu, see "Main menu" below |

### Main menu
One `<nav class="cpe-menu" id="cpe-menu">` per page (both headers), styled by `assets/css/menu.css` and driven by the main-menu block in `assets/js/main.js`. Enqueue `menu.css` on every page. Every link is in the server HTML; closed panels are hidden with CSS only, and no links are injected by JavaScript.

- **Menu items** (WordPress menu): Rental › Boom Lifts › Telescopic / Articulated / Electric; Rental › Scissor Lifts › Slab Electric / Rough Terrain Electric / Diesel 4x4; Rental › Spider Lifts (no children); Sales › …; Services › …; About; Blog; Contact. The height range under each rental item is the item description (or computed from the term's machines).
- **Walker output per item with children:** `li.cm-item.cm-has-sub` holding:
  - the page link `a.cm-link` (label `<span>`, optional `<small>` description);
  - a toggle `button.cm-toggle[aria-expanded][aria-controls]` (with the label repeated in `.cm-tlabel` for the mobile row);
  - `div.cm-sub#…` holding:
    - `.cm-head`, with `button.cm-back` ("Back" / "Back to {parent}") and `.cm-title`;
    - `ul.cm-list.cm-l{level}`, with `li.cm-overview` ("Rental overview →" / "View all Boom Lifts →") as its first row, then the children, then the optional `li.cm-more` ("All rental machines →").
- **Items without children:** `li.cm-item > a.cm-link`.
- **Desktop (>960px):** cascading dropdowns.
  - Hover intent: 200 ms before a menu closes or switches to a sibling, so a diagonal move towards a flyout doesn't close it.
  - Flyouts open to the left (`.cm-flip`) when there's no room on the right.
  - Keyboard: arrow keys open and move between items, Esc closes and returns focus to the toggle, and `aria-expanded` is kept in sync.
  - Without JS, menus open on hover or focus.
- **Mobile (≤960px):** the same nav becomes the drawer, opened by `[data-menu-open]` (the burger).
  - Drill-down panels slide in from the right, with a Back button and a panel title.
  - A row with children is one button ("Boom Lifts ›"); the category page itself is the "View all …" row at the top of the next panel.
  - Call and WhatsApp are fixed at the bottom of the drawer.
  - 960px (not 768px) is where the header has no room for the desktop menu, so tablets get the drawer too.

### Redirects (301)
`build.py` writes `_source/redirects.csv` (`source,target,regex,code`) from the data, so every moved URL is covered:
- the 5 old category URLs: `/rental/electric-scissor-lifts/` → `/rental/scissor-lifts/` (that category was split in two), `/rental/rough-terrain-scissor-lifts/` → `/rental/scissor-lifts/diesel-4x4-scissor-lifts/`, and the three boom categories → `/rental/boom-lifts/{child}/`;
- every rental machine: `/rental/{old machine_type}/{slug}/` → `/rental/{slug}/`.

No target is also a source (no chains). Import:
- **Redirection plugin:** Tools → Import → CSV (columns: source, target, regex `0`, code `301`).
- **Rank Math:** Redirections → add each row as a 301 (or use its CSV import and map *source* / *destination*).

If the current live site has other rental URLs (e.g. old category or product pages), add them to the same list before launch.

### Canonicals and sitemap
- Filtered or searched listings (`?m_type=…`, `?q=…`, `?paged=…` on `/rental/all-machines/` and the category pages) are **canonical to the clean URL** and **not in the sitemap**. Don't also set `noindex` on them: a noindex page with a canonical sends Google mixed signals. In Rank Math, check Titles & Meta → the canonical isn't overridden with the query string.
- The mockup writes `sitemap.xml` (all built pages except noindexed ones, never URLs with parameters). In WordPress, Rank Math generates the sitemap: include the `machine_type` taxonomy (parent and child terms) and the `machine` post type; exclude `/sales/new/` while it is noindexed.

### Titles, descriptions and structured data
- Each main-category page has its own `<title>` and meta description (`GROUPS[...]["title"/"desc"]` in `build.py` → Rank Math term SEO fields).
- Main-category pages output **BreadcrumbList** (Home › Rental › {Main}) and **FAQPage** (the visible FAQ) as JSON-LD (`breadcrumb_jsonld()`, `faq_jsonld()`). In WordPress use either Rank Math's schema (breadcrumbs + FAQ block) or the theme's JSON-LD – not both, or Google sees duplicates.

