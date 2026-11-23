/* Cherry Pickers Equipment – machine listings (used, sold, rental). One IIFE, no dependencies.
 *
 * WordPress: enqueue as 'cpe-listing' and pass the config with
 *   wp_localize_script('cpe-listing', 'CPE', ['whatsapp' => ..., 'pageType' => ..., 'perPage' => 24, 'nouns' => [...], 'search' => true]);
 * Only renderResults() changes in WordPress (see the banner above it). URL state, history, the search box, chips,
 * the filter drawer, focus handling and analytics work unchanged with server-rendered results.
 *
 * URL params (see _source/WORDPRESS-MAP.md): q, m_type, m_brand, m_year, m_height, m_capacity, m_outreach, m_origin,
 * m_sold_to, m_sold_year, m_availability (comma-separated), m_sort, paged.
 */
(function () {
  'use strict';

  var CFG = window.CPE;
  var form = document.querySelector('[data-cpe-filters]');
  var results = document.getElementById('cpe-results');
  if (!CFG || !form || !results) return;

  var PER_PAGE = CFG.perPage || 24;
  var NOUNS = CFG.nouns || ['machine', 'machines'];
  var HEADER_OFFSET = 84;        // sticky header height (px)
  var DEBOUNCE_MS = 200;

  // URL param -> card data attribute (dataset key) and how it is compared. Mirrors FIELDS in build.py.
  //   tax = taxonomy slug · range = 'min-max' (min inclusive, max exclusive, open ends empty)
  //   slug = slug of the text value · year = first 4 chars of 'YYYY-MM'. Empty text/date values = 'not-recorded'.
  var FIELDS = {
    m_type: { attr: 'machineType', kind: 'tax', label: 'Machine type' },
    m_brand: { attr: 'machineBrand', kind: 'tax', label: 'Brand' },
    m_year: { attr: 'year', kind: 'range', label: 'Year', unit: '' },
    m_height: { attr: 'workingHeight', kind: 'range', label: 'Working height', unit: ' m' },
    m_capacity: { attr: 'capacity', kind: 'range', label: 'Platform capacity', unit: ' kg' },
    m_outreach: { attr: 'outreach', kind: 'range', label: 'Horizontal outreach', unit: ' m' },
    m_origin: { attr: 'origin', kind: 'slug', label: 'Machine origin' },
    m_sold_to: { attr: 'soldTo', kind: 'slug', label: 'Sold to' },
    m_sold_year: { attr: 'soldDate', kind: 'year', label: 'Year sold' },
    m_availability: { attr: 'availability', kind: 'slug', label: 'Availability' }
  };
  var FIELD_KEYS = Object.keys(FIELDS);
  var OWN_PARAMS = ['q', 'm_sort', 'paged'].concat(FIELD_KEYS);

  // ---------- elements outside #cpe-results (never swapped) ----------
  var inputs = Array.prototype.slice.call(form.querySelectorAll('input[type=checkbox][name]'));
  var sortSel = document.querySelector('[data-cpe-sort]');
  var searchInput = document.querySelector('[data-cpe-search]');
  var clearBtn = document.querySelector('[data-cpe-search-clear]');
  var chipsEl = document.querySelector('[data-cpe-chips]');
  var announceEl = document.querySelector('[data-cpe-announce]');
  var applyBtns = Array.prototype.slice.call(document.querySelectorAll('[data-cpe-filter-apply]'));
  var sortValues = sortSel ? Array.prototype.map.call(sortSel.options, function (o) { return o.value; }) : [];
  var defaultSort = sortValues[0] || '';

  form.classList.add('is-enhanced');

  // ---------- small helpers ----------
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function slugify(s) { return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, ''); }
  function camel(s) { return s.replace(/[_-]([a-z])/g, function (m, c) { return c.toUpperCase(); }); }
  function countLabel(n) { return n + ' ' + (n === 1 ? NOUNS[0] : NOUNS[1]); }
  function hasFilters(s) { return FIELD_KEYS.some(function (k) { return s.filters[k] && s.filters[k].length; }); }
  function boxFor(name, value) {
    for (var i = 0; i < inputs.length; i++) { if (inputs[i].name === name && inputs[i].value === value) return inputs[i]; }
    return null;
  }

  // =====================================================================================================
  // STATE <-> URL  (pure; no rendering)
  // =====================================================================================================
  // Accepts comma lists (?m_type=a,b) and repeated keys (?m_type=a&m_type=b, what a no-JS form submit sends).
  function readParams(search) {
    var p = new URLSearchParams(search);
    var s = { q: (p.get('q') || '').trim(), filters: {}, sort: defaultSort, paged: 1 };
    FIELD_KEYS.forEach(function (k) {
      var vals = [];
      p.getAll(k).forEach(function (v) {
        v.split(',').forEach(function (x) { x = x.trim(); if (x && vals.indexOf(x) < 0) vals.push(x); });
      });
      if (vals.length) s.filters[k] = vals;
    });
    var so = p.get('m_sort');
    if (so && sortValues.indexOf(so) >= 0) s.sort = so;
    var pg = parseInt(p.get('paged'), 10);
    if (pg > 1) s.paged = pg;
    return s;
  }

  // Query string for a state. Other params already in the URL (e.g. utm_*) are kept. paged is dropped on page 1.
  function buildQuery(s) {
    var p = new URLSearchParams(location.search);
    OWN_PARAMS.forEach(function (k) { p.delete(k); });
    if (s.q) p.set('q', s.q);
    FIELD_KEYS.forEach(function (k) { if (s.filters[k] && s.filters[k].length) p.set(k, s.filters[k].join(',')); });
    if (s.sort && s.sort !== defaultSort) p.set('m_sort', s.sort);
    if (s.paged > 1) p.set('paged', String(s.paged));
    return p.toString().replace(/%2C/gi, ',');   // keep comma lists readable
  }
  function buildUrl(s) {
    var q = buildQuery(s);
    return location.pathname + (q ? '?' + q : '') + location.hash;
  }
  function withState(s, changes) {
    var c = { q: s.q, filters: s.filters, sort: s.sort, paged: s.paged };
    for (var k in changes) c[k] = changes[k];
    return c;
  }

  var state = readParams(location.search);

  // History: pushState for discrete actions (page, checkbox, sort, chips, clear), replaceState while typing.
  function commit(mode) {
    if (!mode || !window.history.pushState) return;
    var url = buildUrl(state);
    if (url === location.pathname + location.search + location.hash) return;
    history[mode === 'push' ? 'pushState' : 'replaceState'](null, '', url);
  }

  // =====================================================================================================
  // MOCKUP DATA: the cards already in the page (WordPress does not need this block)
  // =====================================================================================================
  var grid = results.querySelector('[data-cpe-grid]');
  var base = Array.prototype.slice.call(results.querySelectorAll('[data-cpe-item]'));   // server order = default sort
  base.forEach(function (el, i) { el.cpeIndex = i; });

  // Search: ignore case, spaces, hyphens, # and dots ("e 450", "E-450" and "e450" all find "JLG E450AJ").
  function norm(s) { return String(s || '').toLowerCase().replace(/[\s\-#.]+/g, ''); }
  var haystacks = base.map(function (el) {
    var d = el.dataset;
    return [d.model, d.machineBrand, d.origin, d.soldTo, (d.year || '') + ' ' + (d.model || '')]
      .filter(Boolean).map(norm);
  });
  // Whole query first. Only if nothing matches and there are several words, every word must match somewhere
  // ("860sj denmark"). This keeps "e 450" from matching "M450AJ" through the separate words "e" and "450".
  function searchHits(q) {
    var whole = norm(q);
    if (!whole) return null;
    var hit = haystacks.map(function (h) { return h.some(function (x) { return x.indexOf(whole) >= 0; }); });
    if (hit.some(Boolean)) return hit;
    var words = q.trim().split(/\s+/).map(norm).filter(Boolean);
    if (words.length < 2) return hit;
    return haystacks.map(function (h) {
      return words.every(function (w) { return h.some(function (x) { return x.indexOf(w) >= 0; }); });
    });
  }

  function inRange(v, r) {
    var n = parseFloat(v), ab = r.split('-');
    if (isNaN(n) || ab.length !== 2) return false;
    return (ab[0] === '' || n >= parseFloat(ab[0])) && (ab[1] === '' || n < parseFloat(ab[1]));
  }
  function facetMatch(el, key, value) {
    var f = FIELDS[key], v = el.dataset[f.attr];
    if (f.kind === 'range') return inRange(v, value);
    if (f.kind === 'tax') return v === value;
    if (f.kind === 'year') return (v ? v.slice(0, 4) : 'not-recorded') === value;
    return (v ? slugify(v) : 'not-recorded') === value;
  }
  // OR inside a group, AND across groups. skip = leave one group out (for that group's own counts).
  function passFilters(el, filters, skip) {
    for (var k in filters) {
      if (k === skip || !filters[k].length) continue;
      if (!filters[k].some(function (v) { return facetMatch(el, k, v); })) return false;
    }
    return true;
  }
  function sortNum(v) { var n = parseFloat(String(v == null ? '' : v).replace(/-/g, '')); return isNaN(n) ? 0 : n; }
  // Stable sort on a data attribute: 'year-desc', 'working_height-asc', 'sold_date-desc' (mirrors sort_items() in build.py)
  function sortItems(list, sort) {
    var i = sort.lastIndexOf('-'), key = camel(sort.slice(0, i)), desc = sort.slice(i + 1) === 'desc';
    return list.map(function (el) { return { el: el, v: sortNum(el.dataset[key]) }; })
      .sort(function (a, b) { return (desc ? b.v - a.v : a.v - b.v) || a.el.cpeIndex - b.el.cpeIndex; })
      .map(function (x) { return x.el; });
  }

  function headingText(total, paged) {
    if (total <= PER_PAGE) return 'Showing ' + countLabel(total);
    var a = (paged - 1) * PER_PAGE + 1;
    return 'Showing ' + a + '–' + Math.min(total, paged * PER_PAGE) + ' of ' + countLabel(total);
  }

  // 1 … 4 5 6 … 9 (null = gap; a gap of one page shows that page). Mirrors page_list() in build.py.
  function pageList(cur, last) {
    var keep = [1, last, cur - 1, cur, cur + 1].filter(function (p, i, a) { return p >= 1 && p <= last && a.indexOf(p) === i; })
      .sort(function (a, b) { return a - b; });
    var out = [], prev = 0;
    keep.forEach(function (p) {
      if (p - prev === 2) out.push(prev + 1); else if (p - prev > 2) out.push(null);
      out.push(p); prev = p;
    });
    return out;
  }
  // Same markup as listing_pagination() in build.py / template-parts/pagination.php
  function paginationHtml(s, total, cur) {
    var last = Math.ceil(total / PER_PAGE);
    if (last <= 1) return '';
    function href(p) { return '?' + buildQuery(withState(s, { paged: p })); }
    var lab = function (t) { return '<span class="cpe-listing-pagination__label">' + t + '</span>'; };
    var prev = cur > 1
      ? '<a class="cpe-listing-pagination__prev" href="' + esc(href(cur - 1)) + '" rel="prev" data-cpe-page="' + (cur - 1) + '">‹ ' + lab('Previous') + '</a>'
      : '<span class="cpe-listing-pagination__prev is-disabled" aria-disabled="true">‹ ' + lab('Previous') + '</span>';
    var next = cur < last
      ? '<a class="cpe-listing-pagination__next" href="' + esc(href(cur + 1)) + '" rel="next" data-cpe-page="' + (cur + 1) + '">' + lab('Next') + ' ›</a>'
      : '<span class="cpe-listing-pagination__next is-disabled" aria-disabled="true">' + lab('Next') + ' ›</span>';
    var pages = pageList(cur, last).map(function (p) {
      if (p === null) return '<li><span class="cpe-listing-pagination__gap" aria-hidden="true">…</span></li>';
      if (p === cur) return '<li><span class="cpe-listing-pagination__page is-current" aria-current="page">' + p + '</span></li>';
      return '<li><a class="cpe-listing-pagination__page" href="' + esc(href(p)) + '" data-cpe-page="' + p + '" aria-label="Page ' + p + '">' + p + '</a></li>';
    }).join('');
    return '<nav class="cpe-listing-pagination" aria-label="Pagination">' + prev +
      '<ul class="cpe-listing-pagination__pages">' + pages + '</ul>' +
      '<span class="cpe-listing-pagination__status">Page ' + cur + ' of ' + last + '</span>' + next + '</nav>';
  }

  // No-results block: fill the search term into the title, the quote link and the WhatsApp text.
  var emptyEl = results.querySelector('[data-cpe-empty]');
  var quoteBase = emptyEl && emptyEl.querySelector('[data-cpe-empty-quote]').getAttribute('href');
  function renderEmpty(s, total) {
    if (!emptyEl) return;
    emptyEl.hidden = total > 0;
    if (total > 0) return;
    var q = s.q, d = emptyEl.dataset;
    emptyEl.querySelector('[data-cpe-empty-title]').textContent = q ? d.titleTerm.replace('{term}', q) : d.title;
    var u = new URL(quoteBase, location.href);
    if (q) u.searchParams.set('machine', q); else u.searchParams.delete('machine');
    emptyEl.querySelector('[data-cpe-empty-quote]').href = u.href;
    emptyEl.querySelector('[data-cpe-empty-wa]').href = 'https://wa.me/' + CFG.whatsapp + '?text=' +
      encodeURIComponent(q ? d.waTerm.replace('{term}', q) : d.wa);
    emptyEl.querySelector('[data-cpe-clear-filters]').hidden = !hasFilters(s);
  }

  // Sidebar counts: each option counted against the search + all *other* filter groups.
  function renderFacetCounts(s, hits) {
    inputs.forEach(function (inp) {
      var n = 0;
      base.forEach(function (el, i) {
        if ((!hits || hits[i]) && passFilters(el, s.filters, inp.name) && facetMatch(el, inp.name, inp.value)) n++;
      });
      var c = inp.parentNode.querySelector('.count');
      if (c) c.textContent = n;
      inp.parentNode.classList.toggle('is-zero', n === 0 && !inp.checked);
    });
  }

  /* =====================================================================================================
   * renderResults(state) -> Promise<{ total, paged }>
   *
   * THE ONLY FUNCTION THAT CHANGES IN WORDPRESS. Replace its body with a fetch of the same URL and a swap of
   * #cpe-results (the server renders heading, cards, empty state and pagination for the request):
   *
   *   return fetch(buildUrl(s), { headers: { 'X-Requested-With': 'cpe-listing' } })
   *     .then(function (r) { return r.text(); })
   *     .then(function (html) {
   *       var doc = new DOMParser().parseFromString(html, 'text/html');
   *       var fresh = doc.getElementById('cpe-results');
   *       results.innerHTML = fresh.innerHTML;
   *       results.dataset.total = fresh.dataset.total;
   *       results.dataset.paged = fresh.dataset.paged;
   *       // + update the sidebar counts returned with the response (see WORDPRESS-MAP.md)
   *       return { total: +fresh.dataset.total, paged: +fresh.dataset.paged };
   *     });
   *
   * In this mockup it filters, sorts and paginates the cards that are already in the page.
   * ===================================================================================================== */
  function renderResults(s) {
    var hits = searchHits(s.q);
    var sorted = sortItems(base, s.sort);
    var vis = sorted.filter(function (el) { return (!hits || hits[el.cpeIndex]) && passFilters(el, s.filters); });
    var total = vis.length;
    var last = Math.max(1, Math.ceil(total / PER_PAGE));
    var paged = Math.min(Math.max(1, s.paged), last);          // out-of-range ?paged= -> last page
    var start = (paged - 1) * PER_PAGE, shown = vis.slice(start, start + PER_PAGE);

    sorted.forEach(function (el) { grid.appendChild(el); });
    base.forEach(function (el) { el.hidden = true; });
    shown.forEach(function (el) { el.hidden = false; });

    results.querySelector('[data-cpe-heading]').textContent = headingText(total, paged);
    results.dataset.total = total;
    results.dataset.paged = paged;
    renderEmpty(s, total);
    results.querySelector('[data-cpe-pager]').innerHTML = paginationHtml(withState(s, { paged: paged }), total, paged);
    renderFacetCounts(s, hits);
    return Promise.resolve({ total: total, paged: paged });
  }

  // =====================================================================================================
  // EVERYTHING BELOW IS INDEPENDENT OF HOW RESULTS ARE RENDERED
  // =====================================================================================================
  function syncForm() {
    inputs.forEach(function (i) { i.checked = (state.filters[i.name] || []).indexOf(i.value) >= 0; });
    if (sortSel) sortSel.value = state.sort;
    if (searchInput && searchInput.value.trim() !== state.q) searchInput.value = state.q;
    updateClearBtn();
  }
  // Filters from the checkboxes; values with no checkbox on this page (e.g. m_height=12-20 from the home finder) are kept.
  function filtersFromForm() {
    var f = {};
    FIELD_KEYS.forEach(function (k) {
      var orphans = (state.filters[k] || []).filter(function (v) { return !boxFor(k, v); });
      if (orphans.length) f[k] = orphans;
    });
    inputs.forEach(function (i) { if (i.checked) (f[i.name] = f[i.name] || []).push(i.value); });
    return f;
  }

  function valueLabel(key, v) {
    var f = FIELDS[key];
    if (f.kind === 'range') {
      var ab = v.split('-'), u = f.unit || '';
      if (ab[0] === '' || ab[0] === '0') return 'up to ' + ab[1] + u;
      if (ab[1] === '') return ab[0] + u + ' and above';
      return ab[0] + ' – ' + ab[1] + u;
    }
    var t = v.replace(/-/g, ' ');
    return t.charAt(0).toUpperCase() + t.slice(1);
  }
  function renderChips() {
    if (!chipsEl) return;
    chipsEl.innerHTML = '';
    FIELD_KEYS.forEach(function (k) {
      (state.filters[k] || []).forEach(function (v) {
        var box = boxFor(k, v);
        var label = box ? box.parentNode.getAttribute('data-label') : FIELDS[k].label + ': ' + valueLabel(k, v);
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'chip chip--active';
        b.textContent = label + '  ×';
        b.setAttribute('aria-label', 'Remove filter: ' + label);
        b.addEventListener('click', function () {
          var rest = state.filters[k].filter(function (x) { return x !== v; }), f = {};
          for (var key in state.filters) f[key] = state.filters[key];
          if (rest.length) f[k] = rest; else delete f[k];
          state = withState(state, { filters: f, paged: 1 });
          syncForm();
          update({ history: 'push', announce: true });
        });
        chipsEl.appendChild(b);
      });
    });
  }

  function announce(msg) {
    if (!announceEl) return;
    announceEl.textContent = '';
    setTimeout(function () { announceEl.textContent = msg; }, 60);   // re-announces an unchanged message too
  }
  function focusResults() {
    var top = results.getBoundingClientRect().top + window.pageYOffset - HEADER_OFFSET;
    window.scrollTo(0, Math.max(0, top));
    var h = results.querySelector('[data-cpe-heading]');
    if (h) h.focus({ preventScroll: true });
  }

  // GA4: one push per debounced search of 2+ characters (and for ?q= on load). The same term is not pushed twice in a row.
  var lastTracked = null;
  function track(source, total) {
    if (!source || state.q.length < 2 || state.q === lastTracked) return;
    lastTracked = state.q;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: 'search_listing', page_type: CFG.pageType, search_term: state.q,
      results_count: total, search_source: source });
  }

  // One entry point for every change: render, then URL / chips / counts / focus / announcement / analytics.
  // opts: history 'push'|'replace'|null · focus (pagination only) · announce · track ('typed'|'url')
  var seq = 0;
  function update(opts) {
    var mine = ++seq;
    return renderResults(state).then(function (r) {
      if (mine !== seq) return r;                 // a newer request has started (matters for fetch in WordPress)
      state.paged = r.paged;
      commit(opts.history);
      applyBtns.forEach(function (b) { b.textContent = 'Show ' + countLabel(r.total); });
      renderChips();
      if (opts.focus) focusResults();
      else if (opts.announce) announce(countLabel(r.total) + ' found');
      track(opts.track, r.total);
      return r;
    });
  }

  // ---------- search box ----------
  var timer = null;
  function updateClearBtn() { if (clearBtn && searchInput) clearBtn.hidden = !searchInput.value; }
  function runSearch(source) {
    clearTimeout(timer);
    var q = searchInput.value.trim();
    if (q === state.q) return;
    if (!q) lastTracked = null;
    state = withState(state, { q: q, paged: 1 });
    update({ history: 'replace', announce: true, track: source });
  }
  function clearSearch() {
    searchInput.value = '';
    updateClearBtn();
    runSearch(null);
    searchInput.focus();
  }
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      updateClearBtn();
      clearTimeout(timer);
      timer = setTimeout(function () { runSearch('typed'); }, DEBOUNCE_MS);
    });
    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && searchInput.value) { e.preventDefault(); clearSearch(); }
    });
  }
  if (clearBtn) clearBtn.addEventListener('click', clearSearch);

  // ---------- filters, sort, clear ----------
  inputs.forEach(function (i) {
    i.addEventListener('change', function () {
      state = withState(state, { filters: filtersFromForm(), paged: 1 });
      update({ history: 'push', announce: true });
    });
  });
  if (sortSel) sortSel.addEventListener('change', function () {
    state = withState(state, { sort: sortSel.value, paged: 1 });
    update({ history: 'push', announce: true });
  });
  // Enter in the search box (implicit submit) or the drawer's "Show N machines" button
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (searchInput && document.activeElement === searchInput) runSearch('typed');
    else form.classList.remove('open');
  });
  // "Clear all": filters and search (sort stays)
  form.querySelectorAll('[data-cpe-clear-all]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      if (searchInput) { searchInput.value = ''; lastTracked = null; }
      state = withState(state, { q: '', filters: {}, paged: 1 });
      syncForm();
      update({ history: 'push', announce: true });
    });
  });

  // Inside #cpe-results (swapped in WordPress) -> delegated listeners
  results.addEventListener('click', function (e) {
    var t = e.target.closest('[data-cpe-page], [data-cpe-try], [data-cpe-clear-filters]');
    if (!t) return;
    if (t.hasAttribute('data-cpe-page')) {
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.button === 1) return;   // let "open in new tab" work
      e.preventDefault();
      state = withState(state, { paged: parseInt(t.getAttribute('data-cpe-page'), 10) || 1 });
      update({ history: 'push', focus: true });
    } else if (t.hasAttribute('data-cpe-try')) {
      // "Try:" chip -> fills the search
      if (!searchInput) return;
      searchInput.value = t.getAttribute('data-cpe-try');
      updateClearBtn();
      runSearch('typed');
      searchInput.focus();
    } else {
      // "Clear filters" in the no-results block: filters only, the search term stays
      state = withState(state, { filters: {}, paged: 1 });
      syncForm();
      update({ history: 'push', announce: true });
    }
  });

  // ---------- filter drawer (mobile) ----------
  document.querySelectorAll('[data-cpe-filter-open]').forEach(function (b) {
    b.addEventListener('click', function () { form.classList.add('open'); });
  });
  form.querySelectorAll('[data-cpe-filter-close]').forEach(function (b) {
    b.addEventListener('click', function () { form.classList.remove('open'); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && form.classList.contains('open')) form.classList.remove('open');
  });

  // ---------- back / forward ----------
  window.addEventListener('popstate', function () {
    state = readParams(location.search);
    syncForm();
    update({ history: null, announce: true });
  });

  // ---------- first render from the URL ----------
  syncForm();
  var arrivedWithParams = OWN_PARAMS.some(function (k) { return new URLSearchParams(location.search).has(k); });
  update({ history: 'replace', track: state.q ? 'url' : null }).then(function () {
    // arriving from the home finder, a shared ?q= link or a page link: bring the listing into view
    if (arrivedWithParams) {
      var sec = form.closest('section') || results;
      window.scrollTo(0, Math.max(0, sec.getBoundingClientRect().top + window.pageYOffset - HEADER_OFFSET));
    }
  });
})();
