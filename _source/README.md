# Mockup source

The HTML pages are generated – edit here, then rebuild:

    cd _source && python3 build.py

- `build.py` – page list, URL map, rental fleet data (R), sales stock (SALE), Rental/Sales landing and listing templates, header/footer
- `legacy.py` – icons, enquiry form and contact strip used by build.py
- `pages/` – hand-written pages (home, about, services, maintenance, blog, contact, legal, detail pages)
- `data/sold.txt` – the 212 sold records from the live Sold page (cleaned)

Note: build.py writes to the folder above `_source/` (`OUT` at the top of both .py files). On Windows use `python build.py`.
Folder URLs mirror the WordPress site: /rental/{category}/, /sales/, /sales/new/, /sales/used/, /sales/sold/.
New equipment: add machines to `NEW` in build.py (same format as `SALE`). While `NEW` is empty, /sales/new/ shows an enquiry panel and is noindexed.
