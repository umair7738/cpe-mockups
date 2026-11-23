# Mockup source

The HTML pages are generated – edit here, then rebuild:

    cd _source && python3 build.py

- `data/machines.json` – all machines (rental fleet, used stock, 212 sold records), shaped like WordPress posts (taxonomies + ACF fields). build.py reads machine data only from this file.
- `build.py` – page list, URL map, listing template parts (`machine_card`, `listing_toolbar`, `listing_filters`, `listing_empty`, `listing_pagination`), Rental/Sales landing and listing pages, header/footer
- `legacy.py` – icons, enquiry form and contact strip used by build.py
- `pages/` – hand-written pages (home, about, services, maintenance, blog, contact, legal, detail pages). Machine cards are included with `{{card:<listing_status>:<slug>}}`, e.g. `{{card:used:2018-jlg-e450aj}}`.
- `WORDPRESS-MAP.md` – how the listing pages map to the WordPress theme: template parts, ACF fields, URL params, `window.CPE`, and the one JS function that changes

Note: build.py writes to the folder above `_source/` (`OUT` at the top of both .py files). On Windows use `python build.py`.
Folder URLs mirror the WordPress site: /rental/{category}/, /sales/, /sales/new/, /sales/used/, /sales/sold/.
New equipment: add machines with `"listing_status": "new"` to `data/machines.json`. While there are none, /sales/new/ shows an enquiry panel and is noindexed.
Listing pages (used, sold, rental) are driven by `assets/js/listing.js`; filters, search and paging are in the URL (`?q=`, `m_*`, `m_sort`, `paged`).
- `quote.py`: markup for the quote popup and the shared quote fields (`{{quotefields:prefix|type|machine|category|notoggle,sold}}` and `{{quote:type|machine|category}}` tokens). `build.py` writes the popup into every page except Contact and copies it to `assets/partials/quote-modal.html`. Behaviour is in `assets/js/quote-modal.js` and the WordPress notes are in `WORDPRESS-MAP.md` section 7.

