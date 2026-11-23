/* Cherry Pickers Equipment – mockup interactions (small, no libraries) */
(function () {
  // Mobile menu
  var toggle = document.querySelector('.menu-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = document.body.classList.toggle('nav-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Machine listings (filters, search, sort, pagination, filter drawer) live in listing.js.

  // Quote forms (contact pre-fill, validation, popup) live in quote-modal.js.

  // ---------- Blog: filter by category (dropdown) + sort ----------
  var posts = document.querySelector('[data-blog-posts]');
  if (posts) {
    var cards = Array.prototype.slice.call(posts.querySelectorAll('.post-card'));
    var blogCat = document.querySelector('[data-blog-cat]');
    var blogSort = document.querySelector('[data-blog-sort]');
    var showPosts = function () {
      var p = blogSort.value.split('-'), key = p[0], cat = blogCat.value;
      cards.slice().sort(function (a, b) {
        var x = parseFloat(a.dataset[key]) || 0, y = parseFloat(b.dataset[key]) || 0;
        return p[1] === 'desc' ? y - x : x - y;
      }).forEach(function (el) { posts.appendChild(el); });
      cards.forEach(function (el) { el.hidden = cat !== 'all' && el.dataset.cat !== cat; });
    };
    blogCat.addEventListener('change', showPosts);
    blogSort.addEventListener('change', showPosts);
    showPosts();
  }

  // Gallery thumbnails: swap the main photo
  document.querySelectorAll('.gallery-thumbs button[data-src]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var wrap = btn.closest('.gallery');
      wrap.querySelectorAll('.gallery-thumbs button').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      var main = wrap.querySelector('.gallery-main img');
      var thumb = btn.querySelector('img');
      if (main) { main.src = btn.getAttribute('data-src'); if (thumb) main.alt = thumb.alt; }
    });
  });

  // About > What we do: cards are white; navy shows on hover / keyboard focus (CSS).
  // On touch screens there is no hover, so a tap highlights that card until another card or the page is tapped.
  document.querySelectorAll('.about-services').forEach(function (grid) {
    var cards = Array.prototype.slice.call(grid.children);
    var activate = function (card) { cards.forEach(function (c) { c.classList.toggle('is-active', c === card); }); };
    document.addEventListener('pointerdown', function (e) {
      if (e.pointerType === 'mouse') return;
      var card = null;
      cards.forEach(function (c) { if (c.contains(e.target)) card = c; });
      activate(card);
    });
  });

  // =====================================================================
  // HOME PAGE (index.html) – each block only runs if its element exists
  // =====================================================================
  // ---------- Header: shrink on scroll ----------
  (function () {
    var hdr = document.getElementById('hdr');
    if (!hdr) return;
    var onScroll = function () { hdr.classList.toggle('shrink', window.scrollY > 40); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  })();

  // ---------- Drawer menu (below 961px) ----------
  (function () {
    var drawer = document.getElementById('drawer'), burger = document.getElementById('burger'), x = document.getElementById('drawerX');
    if (!drawer || !burger || !x) return;
    var open = function () {
      drawer.hidden = false;
      document.body.classList.add('drawer-open');
      burger.setAttribute('aria-expanded', 'true');
      x.focus();
    };
    var close = function (focusBack) {
      if (drawer.hidden) return;
      drawer.hidden = true;
      document.body.classList.remove('drawer-open');
      burger.setAttribute('aria-expanded', 'false');
      if (focusBack) burger.focus();
    };
    burger.addEventListener('click', open);
    x.addEventListener('click', function () { close(true); });
    drawer.addEventListener('click', function (e) { if (e.target === drawer || e.target.closest('a')) close(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(true); });
  })();

  // ---------- Project slider + lightbox ----------
  (function () {
    var track = document.getElementById('track');
    if (!track) return;
    var step = function () {
      var s = track.querySelector('.slide');
      return s ? s.offsetWidth + (parseFloat(getComputedStyle(track).columnGap) || 0) : 300;
    };
    var prev = document.getElementById('sPrev'), next = document.getElementById('sNext');
    if (prev) prev.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: 'smooth' }); });
    if (next) next.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: 'smooth' }); });

    var lb = document.getElementById('lb'), img = document.getElementById('lbImg'), cap = document.getElementById('lbCap'), x = document.getElementById('lbX');
    if (!lb || !img || !cap || !x) return;
    var last = null;
    var open = function (slide) {
      var i = slide.querySelector('img'), b = slide.querySelector('.cap b'), s = slide.querySelector('.cap span');
      img.src = i.currentSrc || i.src;
      img.alt = i.alt;
      cap.textContent = (b ? b.textContent : '') + (s ? ' · ' + s.textContent : '');
      last = slide;
      lb.hidden = false;
      x.focus();
    };
    var close = function () {
      if (lb.hidden) return;
      lb.hidden = true;
      if (last) last.focus();
    };
    track.querySelectorAll('.slide').forEach(function (s) {
      s.addEventListener('click', function () { open(s); });
      s.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(s); }
      });
    });
    x.addEventListener('click', close);
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  })();

  // ---------- Used | New tabs ----------
  (function () {
    var tabs = Array.prototype.slice.call(document.querySelectorAll('.tabs [role=tab]'));
    if (!tabs.length) return;
    var select = function (t, focus) {
      tabs.forEach(function (x) {
        var on = x === t;
        x.classList.toggle('on', on);
        x.setAttribute('aria-selected', on ? 'true' : 'false');
        x.tabIndex = on ? 0 : -1;
        var pane = document.getElementById(x.getAttribute('aria-controls'));
        if (pane) pane.hidden = !on;
      });
      if (focus) t.focus();
    };
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { select(t); });
      t.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
          e.preventDefault();
          select(tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length], true);
        }
      });
    });
  })();

  // ---------- Machine finder: rent -> rental/all-machines/, buy -> sales/used/ with ?m_type=&m_height= ----------
  (function () {
    var finder = document.getElementById('finder');
    if (!finder) return;
    // Working-height options per category (values are "min-max" in metres)
    var HT = {
      '': [['0-12', 'Up to 12 m'], ['12-20', '12 – 20 m'], ['20-30', '20 – 30 m'], ['30-45', '30 m +']],
      'electric-scissor-lifts': [['0-10', 'Up to 10 m'], ['10-12', '10 – 12 m'], ['12-14', '12 – 14 m'], ['14-16', '14 – 15.7 m']],
      'rough-terrain-scissor-lifts': [['15-16', '15 – 16 m'], ['16-18', '16 – 18 m'], ['18-19', '18 m +']],
      'electric-boom-lifts': [['13-16', '13.5 – 16 m'], ['16-18', '16 – 18 m'], ['18-21', '18 – 20.4 m']],
      'articulated-boom-lifts': [['15-20', '15.7 – 20 m'], ['20-26', '20 – 26 m'], ['26-35', '26 – 35 m'], ['35-44', '35 – 43.2 m']],
      'telescopic-boom-lifts': [['15-20', '15.7 – 20 m'], ['20-25', '20 – 25 m'], ['25-29', '25 – 28.2 m']]
    };
    var qW = document.getElementById('qWant'), qC = document.getElementById('qCat'), qH = document.getElementById('qHt');
    var fillHt = function () {
      var keep = qH.value;
      qH.innerHTML = '<option value="">Any height</option>';
      (HT[qC.value] || HT['']).forEach(function (o) {
        var e = document.createElement('option');
        e.value = o[0]; e.textContent = o[1];
        qH.appendChild(e);
      });
      if ([].some.call(qH.options, function (o) { return o.value === keep; })) qH.value = keep;
    };
    qC.addEventListener('change', fillHt);
    fillHt();
    // Listing params (see WORDPRESS-MAP.md): m_type = machine_type slug, m_height = 'min-max' working height in metres
    finder.addEventListener('submit', function (e) {
      e.preventDefault();
      var base = finder.getAttribute(qW.value === 'buy' ? 'data-buy' : 'data-rent'), p = [];
      if (qC.value) p.push('m_type=' + encodeURIComponent(qC.value));
      if (qH.value) p.push('m_height=' + encodeURIComponent(qH.value));
      window.location.href = base + (p.length ? '?' + p.join('&') : '');
    });
  })();

})();
