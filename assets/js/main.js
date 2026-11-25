/* Cherry Pickers Equipment – mockup interactions (small, no libraries) */
(function () {
  // ---------- Main menu (markup: build.py menu_html(), styles: assets/css/menu.css) ----------
  // Desktop (>960px): cascading dropdowns with hover intent, flyouts that flip left near the edge, full keyboard support.
  // Mobile (<=960px): the same <nav> is an off-canvas drawer with drill-down panels and Back buttons.
  // All links are in the HTML; this script only toggles .is-open classes and aria-expanded.
  (function () {
    var nav = document.getElementById('cpe-menu');
    if (!nav) return;
    nav.classList.add('cm-ready');
    var mq = window.matchMedia('(max-width: 960px)');
    var mobile = function () { return mq.matches; };
    var openers = Array.prototype.slice.call(document.querySelectorAll('[data-menu-open]'));
    var closeBtn = nav.querySelector('.cm-close');
    var DELAY = 200;   // hover intent: ms before a menu closes, or before switching to a sibling's flyout
    var lastOpener = null;

    var kids = function (el, sel) { return Array.prototype.filter.call(el.children, function (c) { return c.matches(sel); }); };
    var toggleOf = function (li) { return kids(li, '.cm-toggle')[0]; };
    var subOf = function (li) { return kids(li, '.cm-sub')[0]; };
    var visible = function (el) { return !!(el && el.getClientRects().length); };
    var rows = function (ul) { return kids(ul, 'li').filter(visible); };
    // focus target of a row: its link, or (mobile, rows with a sub-menu) the toggle button
    var entry = function (li) { var a = kids(li, '.cm-link')[0]; return visible(a) ? a : toggleOf(li); };
    var firstRow = function (li) { return rows(subOf(li).querySelector('.cm-list'))[0]; };

    var setOpen = function (li, on) {
      clearTimeout(li.cmTimer);
      li.classList.toggle('is-open', on);
      var t = toggleOf(li);
      if (t) t.setAttribute('aria-expanded', on ? 'true' : 'false');
      if (!on) Array.prototype.forEach.call(li.querySelectorAll('.cm-item.is-open'), function (x) { setOpen(x, false); });
    };
    var siblingOpen = function (li) { return kids(li.parentNode, '.is-open').some(function (x) { return x !== li; }); };
    var closeSiblings = function (li) { kids(li.parentNode, '.is-open').forEach(function (x) { if (x !== li) setOpen(x, false); }); };
    var closeAll = function () { Array.prototype.forEach.call(nav.querySelectorAll('.cm-l1 > .is-open'), function (x) { setOpen(x, false); }); };
    // desktop flyouts open to the right; to the left when there is no room
    var place = function (li) {
      li.classList.remove('cm-flip');
      if (mobile() || li.parentNode.classList.contains('cm-l1')) return;
      if (li.getBoundingClientRect().right + subOf(li).offsetWidth + 16 > document.documentElement.clientWidth) li.classList.add('cm-flip');
    };
    var open = function (li) {
      closeSiblings(li);
      place(li);
      if (mobile()) { var panel = li.parentNode.closest('.cm-sub'); if (panel) panel.scrollTop = 0; }
      setOpen(li, true);
    };

    // ---- desktop: hover intent (mouse only; touch and pen use the toggle buttons)
    Array.prototype.forEach.call(nav.querySelectorAll('.cm-has-sub'), function (li) {
      li.addEventListener('pointerenter', function (e) {
        if (e.pointerType !== 'mouse' || mobile()) return;
        clearTimeout(li.cmTimer);
        if (li.classList.contains('is-open')) return;
        // a sibling's menu is open: wait, so a diagonal move towards that flyout doesn't switch menus
        li.cmTimer = setTimeout(function () { open(li); }, siblingOpen(li) ? DELAY : 40);
      });
      li.addEventListener('pointerleave', function (e) {
        if (e.pointerType !== 'mouse' || mobile()) return;
        clearTimeout(li.cmTimer);
        li.cmTimer = setTimeout(function () { setOpen(li, false); }, DELAY);
      });
    });

    // ---- clicks: toggles (desktop + mobile), Back, close, links
    nav.addEventListener('click', function (e) {
      var t = e.target.closest('.cm-toggle');
      if (t) {
        var li = t.parentNode;
        if (li.classList.contains('is-open')) setOpen(li, false);
        else {
          open(li);
          if (mobile()) subOf(li).querySelector('.cm-back').focus({ preventScroll: true });
        }
        return;
      }
      var back = e.target.closest('.cm-back');
      if (back) { var p = back.closest('.cm-item'); setOpen(p, false); toggleOf(p).focus({ preventScroll: true }); return; }
      if (e.target.closest('.cm-close')) { closeDrawer(true); return; }
      if (e.target.closest('a') && mobile()) closeDrawer(false);
    });
    document.addEventListener('click', function (e) {
      if (nav.contains(e.target) || e.target.closest('[data-menu-open]')) return;
      if (mobile()) closeDrawer(false); else closeAll();
    });

    // ---- keyboard
    nav.addEventListener('keydown', function (e) {
      var li = e.target.closest('li');
      if (e.key === 'Escape') {
        var all = nav.querySelectorAll('.cm-item.is-open');
        var openLi = e.target.closest('.cm-item.is-open') || (mobile() && all.length ? all[all.length - 1] : null);
        if (openLi) { setOpen(openLi, false); toggleOf(openLi).focus(); e.preventDefault(); }
        else if (mobile()) closeDrawer(true);
        return;
      }
      if (mobile() || !li) return;
      var ul = li.parentNode, top = ul.classList.contains('cm-l1'), hasSub = li.classList.contains('cm-has-sub');
      var list = rows(ul), i = list.indexOf(li);
      var go = function (x) { if (x) { entry(x).focus(); e.preventDefault(); } };
      if (e.key === 'ArrowDown') {
        if (top) { if (hasSub) { open(li); go(firstRow(li)); } }
        else go(list[(i + 1) % list.length]);
      } else if (e.key === 'ArrowUp') {
        if (!top) go(list[(i - 1 + list.length) % list.length]);
      } else if (e.key === 'ArrowRight') {
        if (top) go(list[(i + 1) % list.length]);
        else if (hasSub) { open(li); go(firstRow(li)); }
      } else if (e.key === 'ArrowLeft') {
        if (top) go(list[(i - 1 + list.length) % list.length]);
        else {
          var parent = ul.closest('.cm-item');
          if (parent && !parent.parentNode.classList.contains('cm-l1')) { setOpen(parent, false); entry(parent).focus(); e.preventDefault(); }
        }
      }
    });
    // desktop: moving focus to another item closes the other menus at that level; leaving the nav closes all
    nav.addEventListener('focusin', function (e) {
      if (mobile()) return;
      for (var li = e.target.closest('.cm-item'); li; li = li.parentNode.closest('.cm-item')) closeSiblings(li);
    });
    nav.addEventListener('focusout', function (e) { if (!mobile() && !nav.contains(e.relatedTarget)) closeAll(); });

    // ---- mobile drawer
    var setOpeners = function (on) { openers.forEach(function (b) { b.setAttribute('aria-expanded', on ? 'true' : 'false'); }); };
    var openDrawer = function (btn) {
      lastOpener = btn;
      closeAll();
      nav.classList.add('is-open');
      document.body.classList.add('menu-open');
      setOpeners(true);
      closeBtn.focus({ preventScroll: true });
    };
    var closeDrawer = function (focusBack) {
      if (!nav.classList.contains('is-open')) return;
      nav.classList.remove('is-open');
      document.body.classList.remove('menu-open');
      setOpeners(false);
      setTimeout(function () { if (!nav.classList.contains('is-open')) closeAll(); }, 260);  // reset panels after the slide-out
      if (focusBack && lastOpener) lastOpener.focus();
    };
    openers.forEach(function (b) { b.addEventListener('click', function () { openDrawer(b); }); });
    var onMq = function () { closeAll(); closeDrawer(false); };
    if (mq.addEventListener) mq.addEventListener('change', onMq); else mq.addListener(onMq);
  })();

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

  // Detail gallery: thumbnails, prev/next arrows on the main photo, swipe (touch) and arrow keys.
  // Only thumbnails with a real photo (data-src) are slides; grey placeholder slots are skipped.
  document.querySelectorAll('.gallery').forEach(function (wrap) {
    var main = wrap.querySelector('.gallery-main');
    var img = main && main.querySelector('img');
    var thumbs = Array.prototype.slice.call(wrap.querySelectorAll('.gallery-thumbs button[data-src]'));
    if (!img || !thumbs.length) return;
    var cur = Math.max(0, thumbs.findIndex(function (b) { return b.classList.contains('active'); }));
    var count;
    var show = function (i) {
      cur = (i + thumbs.length) % thumbs.length;
      var btn = thumbs[cur], t = btn.querySelector('img');
      wrap.querySelectorAll('.gallery-thumbs button').forEach(function (b) { b.classList.remove('active'); b.removeAttribute('aria-current'); });
      btn.classList.add('active');
      btn.setAttribute('aria-current', 'true');
      img.src = btn.getAttribute('data-src');
      if (t) img.alt = t.alt;
      if (count) count.textContent = (cur + 1) + ' / ' + thumbs.length;
    };
    thumbs.forEach(function (btn, i) { btn.addEventListener('click', function () { show(i); }); });
    if (thumbs.length < 2) return;

    var arrow = function (dir, label, path) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'gallery-nav gallery-nav--' + dir;
      b.setAttribute('aria-label', label);
      b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="' + path + '"/></svg>';
      b.addEventListener('click', function () { show(cur + (dir === 'next' ? 1 : -1)); });
      main.appendChild(b);
    };
    arrow('prev', 'Previous photo', 'M15 18l-6-6 6-6');
    arrow('next', 'Next photo', 'M9 6l6 6-6 6');
    count = document.createElement('span');
    count.className = 'gallery-count';
    count.setAttribute('aria-live', 'polite');
    main.appendChild(count);
    show(cur);

    // arrow keys while focus is anywhere in the gallery
    wrap.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); show(cur + (e.key === 'ArrowRight' ? 1 : -1)); }
    });
    // horizontal swipe on the main photo (vertical moves still scroll the page)
    var x0 = null, y0 = 0;
    main.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
    main.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) show(cur + (dx < 0 ? 1 : -1));
      x0 = null;
    }, { passive: true });
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

  // ---------- Detail tabs (About | Specifications …) – one group per [data-tabs]; panels show without JS ----------
  document.querySelectorAll('[data-tabs]').forEach(function (group) {
    var tabs = Array.prototype.slice.call(group.querySelectorAll('[role=tab]'));
    if (!tabs.length) return;
    var select = function (t, focus) {
      tabs.forEach(function (x) {
        var on = x === t;
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
        var n = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : null;
        if (n === null) return;
        e.preventDefault();
        select(tabs[(n + tabs.length) % tabs.length], true);
      });
    });
    select(tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0] || tabs[0]);
  });

  // ---------- Machine finder: rent -> rental/all-machines/, buy -> sales/used/ with ?m_type=&m_height= ----------
  (function () {
    var finder = document.getElementById('finder');
    if (!finder) return;
    // Working-height options per category (values are "min-max" in metres)
    var HT = {
      '': [['0-12', 'Up to 12 m'], ['12-20', '12 – 20 m'], ['20-30', '20 – 30 m'], ['30-45', '30 m +']],
      'telescopic-boom-lifts': [['15-20', '15.7 – 20 m'], ['20-25', '20 – 25 m'], ['25-29', '25 – 28.2 m']],
      'articulated-boom-lifts': [['15-20', '15.7 – 20 m'], ['20-26', '20 – 26 m'], ['26-35', '26 – 35 m'], ['35-44', '35 – 43.2 m']],
      'electric-boom-lifts': [['13-16', '13.5 – 16 m'], ['16-18', '16 – 18 m'], ['18-21', '18 – 20.4 m']],
      'slab-electric-scissor-lifts': [['0-10', 'Up to 10 m'], ['10-12', '10 – 11.8 m']],
      'rough-terrain-electric-scissor-lifts': [['13-14', '13.8 – 14 m'], ['14-16', '14 – 15.7 m']],
      'diesel-4x4-scissor-lifts': [['15-16', '15 – 16 m'], ['16-18', '16 – 18 m'], ['18-19', '18 m +']]
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
