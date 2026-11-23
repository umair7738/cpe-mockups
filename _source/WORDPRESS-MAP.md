# WordPress map: machine listings

How the mockup's listing pages (`/sales/used/`, `/sales/sold/`, `/rental/{category}/`, `/rental/`) map to the custom theme.
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
| `machine_type` | `electric-scissor-lifts` Electric Scissor Lift · `rough-terrain-scissor-lifts` Rough Terrain Scissor Lift · `electric-boom-lifts` Electric Boom Lift · `articulated-boom-lifts` Articulated Boom Lift · `telescopic-boom-lifts` Telescopic Boom Lift |
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
| `stock_no` | text | (none yet) | all empty, and not displayed (business decision) |
| `photo_count` | number | (none yet) | all empty |
| `image` | image | all | Mockup: an image basename in `assets/img/` (the `-sm` variant is used on cards). For sold records this is a photo of the **model**, not the unit. |

### Permalinks (custom rewrite rules)
- Rental: `/rental/{machine_type}/{slug}/`
- Others: `/sales/{listing_status}/{slug}/`

### Slugs must be unique per post type
**These 11 slugs appear in both used and sold:**
`2006-genie-s-65`, `2006-jlg-1350sjp`, `2007-jlg-660sj`, `2007-jlg-860sj`, `2007-jlg-860sj-2`, `2008-jlg-1200sjp`, `2008-jlg-660sj`, `2009-jlg-1350sjp`, `2010-jlg-600aj`, `2011-jlg-860sj`, `2018-jlg-e450aj`.

In a single `machine` post type, WordPress would add `-2` to the second post and change its URL. Decide before import. Either:
- keep the used and sold URLs as they are with a custom unique slug (e.g. a hidden prefix stripped by the rewrite), or
- accept new sold URLs and add redirects.

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
