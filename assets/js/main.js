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

  // Filter drawer (mobile)
  var filters = document.querySelector('.filters');
  document.querySelectorAll('[data-filter-open]').forEach(function (b) {
    b.addEventListener('click', function () { filters && filters.classList.add('open'); });
  });
  document.querySelectorAll('[data-filter-close], [data-filter-dismiss]').forEach(function (b) {
    b.addEventListener('click', function () { filters && filters.classList.remove('open'); });
  });

  // ---------- Listing filters: live results + live counts (OR inside a group, AND across groups) ----------
  var listing = document.querySelector('[data-listing]');
  if (listing) {
    var items = Array.prototype.slice.call(listing.querySelectorAll('[data-item]'));
    var facets = items.map(function (el) {
      var f = {};
      (el.getAttribute('data-facets') || '').split(' ').forEach(function (p) {
        if (!p) return; var i = p.indexOf('='); f[p.slice(0, i)] = p.slice(i + 1);
      });
      return f;
    });
    var inputs = Array.prototype.slice.call(document.querySelectorAll('.filters input[type=checkbox][name]'));
    var countEl = document.querySelector('[data-result-count]');
    var showBtns = document.querySelectorAll('[data-filter-close]');
    var empty = document.querySelector('[data-empty]');
    var more = document.querySelector('[data-more]');
    var chips = document.querySelector('[data-active-chips]');
    var sortSel = document.querySelector('[data-sort]');
    var size = parseInt(listing.getAttribute('data-page-size'), 10) || 9999;
    var noun = listing.getAttribute('data-noun') || 'machines';
    var limit = size;

    var selected = function () {
      var s = {};
      inputs.forEach(function (i) { if (i.checked) (s[i.name] = s[i.name] || []).push(i.value); });
      return s;
    };
    var match = function (f, s, skip) {
      for (var k in s) { if (k !== skip && s[k].indexOf(f[k]) < 0) return false; }
      return true;
    };

    // Presets from the URL query, set by the home page machine finder:
    //   ?category=<category-slug>   ticks the matching "Machine type" box (or filters by it if the page has no such box)
    //   ?height=<min-max>           metres; shows machines with min <= working height < max
    var params = new URLSearchParams(location.search);
    var pre = { cat: null, hmin: null, hmax: null };
    var qCat = (params.get('category') || '').toLowerCase();
    if (/^[a-z0-9-]+$/.test(qCat)) {
      var box = inputs.filter(function (i) { return i.name === 'category' && i.value === qCat; })[0];
      if (box) box.checked = true; else pre.cat = qCat;
    }
    var qHt = (params.get('height') || '').match(/^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/);
    if (qHt && parseFloat(qHt[1]) < parseFloat(qHt[2])) { pre.hmin = parseFloat(qHt[1]); pre.hmax = parseFloat(qHt[2]); }
    var preOk = function (el, f) {
      if (pre.cat !== null && f.category !== pre.cat) return false;
      if (pre.hmin !== null) {
        var h = parseFloat(el.getAttribute('data-s-height'));
        if (!(h >= pre.hmin && h < pre.hmax)) return false;
      }
      return true;
    };
    var syncUrl = function () {  // drop removed presets from the address bar so a reload doesn't bring them back
      if (!window.history.replaceState) return;
      var p = new URLSearchParams(location.search);
      if (pre.hmin === null) p.delete('height');
      if (pre.cat === null && !inputs.some(function (i) { return i.name === 'category' && i.checked; })) p.delete('category');
      var q = p.toString();
      history.replaceState(null, '', location.pathname + (q ? '?' + q : '') + location.hash);
    };
    var addChip = function (label, onRemove) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'chip chip--active';
      b.textContent = label + '  ×';
      b.setAttribute('aria-label', 'Remove filter: ' + label);
      b.addEventListener('click', function () { onRemove(); syncUrl(); apply(true); });
      chips.appendChild(b);
    };

    var apply = function (reset) {
      if (reset) limit = size;
      var s = selected();
      var vis = items.filter(function (el, i) { return preOk(el, facets[i]) && match(facets[i], s); });
      if (sortSel) {
        var parts = sortSel.value.split('-'), key = 's' + parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
        vis.sort(function (a, b) {
          var x = parseFloat(a.dataset[key]) || 0, y = parseFloat(b.dataset[key]) || 0;
          return parts[1] === 'desc' ? y - x : x - y;
        });
        vis.forEach(function (el) { el.parentNode.appendChild(el); });
      }
      items.forEach(function (el) { el.hidden = true; });
      vis.forEach(function (el, i) { el.hidden = i >= limit; });
      inputs.forEach(function (inp) {
        var n = facets.filter(function (f, j) { return preOk(items[j], f) && match(f, s, inp.name) && f[inp.name] === inp.value; }).length;
        var c = inp.parentNode.querySelector('.count'); if (c) c.textContent = n;
        inp.parentNode.classList.toggle('is-zero', n === 0 && !inp.checked);
      });
      if (countEl) countEl.textContent = vis.length;
      showBtns.forEach(function (b) { b.textContent = 'Show ' + vis.length + ' ' + noun; });
      if (empty) empty.hidden = vis.length > 0;
      if (more) more.hidden = vis.length <= limit;
      if (chips) {
        chips.innerHTML = '';
        if (pre.cat !== null) {
          var cn = pre.cat.replace(/-/g, ' ');
          addChip('Machine type: ' + cn.charAt(0).toUpperCase() + cn.slice(1), function () { pre.cat = null; });
        }
        if (pre.hmin !== null) {
          addChip('Working height: ' + (pre.hmin === 0 ? 'up to ' + pre.hmax : pre.hmin + ' – ' + pre.hmax) + ' m',
            function () { pre.hmin = pre.hmax = null; });
        }
        inputs.filter(function (i) { return i.checked; }).forEach(function (i) {
          addChip(i.parentNode.getAttribute('data-label'), function () { i.checked = false; });
        });
      }
    };
    inputs.forEach(function (i) { i.addEventListener('change', function () { apply(true); syncUrl(); }); });
    if (sortSel) sortSel.addEventListener('change', function () { apply(false); });
    if (more) more.addEventListener('click', function () { limit += size; apply(false); });
    document.querySelectorAll('[data-clear]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        inputs.forEach(function (i) { i.checked = false; });
        pre.cat = pre.hmin = pre.hmax = null;
        syncUrl(); apply(true);
      });
    });
    // Preset from link, e.g. #category-telescopic-boom-lifts (from the Sales category cards);
    // commas tick several boxes, e.g. #category-electric-scissor-lifts,rough-terrain-scissor-lifts
    var presetFromHash = function () {
      var h = decodeURIComponent((location.hash || '').slice(1)), d = h.indexOf('-');
      if (d < 1) return;
      var key = h.slice(0, d), vals = h.slice(d + 1).split(',');
      inputs.forEach(function (i) { if (i.name === key && vals.indexOf(i.value) >= 0) i.checked = true; });
    };
    presetFromHash();
    window.addEventListener('hashchange', function () { inputs.forEach(function (i) { i.checked = false; }); presetFromHash(); apply(true); });
    apply(true);
    // Arriving from the finder: bring the filtered list into view (below the sticky header)
    if (params.has('category') || params.has('height')) {
      var sec = listing.closest('section') || listing;
      window.scrollTo(0, Math.max(0, sec.getBoundingClientRect().top + window.pageYOffset - 84));
    }
  }

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

  // About > What we do: the navy highlight moves to the last card hovered / focused / tapped and stays there
  document.querySelectorAll('.about-services').forEach(function (grid) {
    var cards = Array.prototype.slice.call(grid.children);
    var activate = function (card) { cards.forEach(function (c) { c.classList.toggle('is-active', c === card); }); };
    cards.forEach(function (c) {
      ['mouseenter', 'focusin', 'click'].forEach(function (ev) { c.addEventListener(ev, function () { activate(c); }); });
    });
  });

  // Forms (mockup only – nothing is sent)
  document.querySelectorAll('form[data-mock]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var ok = f.querySelector('.form-ok');
      if (ok) ok.style.display = 'block';
    });
  });

  // =====================================================================
  // HOME PAGE (index.html) – each block only runs if its element exists
  // =====================================================================
  var WA_NUMBER = '971561018428';

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

  // ---------- Machine finder: rent -> rental/, buy -> sales/used/ with ?category=&height= ----------
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
    finder.addEventListener('submit', function (e) {
      e.preventDefault();
      var base = finder.getAttribute(qW.value === 'buy' ? 'data-buy' : 'data-rent'), p = [];
      if (qC.value) p.push('category=' + encodeURIComponent(qC.value));
      if (qH.value) p.push('height=' + encodeURIComponent(qH.value));
      window.location.href = base + (p.length ? '?' + p.join('&') : '');
    });
  })();

  // ---------- Enquiry form: Rent / Buy / Service, validation, WhatsApp hand-off ----------
  (function () {
    var form = document.getElementById('qform');
    if (!form) return;
    var $ = function (id) { return document.getElementById(id); };
    var fm = $('fm'), fmt = $('fmText'), fml = $('fmLabel'), fdw = $('fDateWrap'), fe = $('fe'), feo = $('feOther'),
        fel = $('feLabel'), fmsg = $('fmsg'), fd = $('fd'), fn = $('fn'), fp = $('fp'), done = $('fDone');
    var want = function () { var r = form.querySelector('input[name=want]:checked'); return r ? r.value : 'rent'; };

    var setWant = function (v) {
      fm.hidden = v !== 'rent';
      fmt.hidden = v === 'rent';
      fml.textContent = v === 'rent' ? 'Machine or height' : v === 'buy' ? 'Machine you want to buy' : 'Your machine (make / model)';
      fml.htmlFor = v === 'rent' ? 'fm' : 'fmText';
      fmt.placeholder = v === 'buy' ? 'e.g. JLG 860SJ' : 'e.g. Genie S-65';
      fdw.hidden = v === 'buy';
      feo.hidden = feo.disabled = v !== 'buy';
      if (v !== 'buy' && fe.selectedIndex === feo.index) fe.selectedIndex = 0;
      fel.textContent = v === 'buy' ? 'Delivery to' : 'Emirate';
      fmsg.placeholder = v === 'rent' ? 'Working height, type of work, site location, hire period'
        : v === 'buy' ? 'Budget, quantity, destination country' : 'Problem, machine location, AMC or one-off repair';
    };
    form.querySelectorAll('input[name=want]').forEach(function (r) {
      r.addEventListener('change', function () { setWant(r.value); });
    });
    setWant(want());

    // "Get a Quote" / "Enquire to Buy" / "Book a service" links preselect the matching option
    document.querySelectorAll('a[data-want]').forEach(function (a) {
      a.addEventListener('click', function () {
        var r = form.querySelector('input[name=want][value="' + a.getAttribute('data-want') + '"]');
        if (r) { r.checked = true; setWant(r.value); }
      });
    });

    var showErr = function (input, errId, bad) {
      var wrap = input.closest('.f'), err = $(errId);
      wrap.classList.toggle('err', bad);
      err.hidden = !bad;
      input.setAttribute('aria-invalid', bad ? 'true' : 'false');
      return bad;
    };
    fn.addEventListener('input', function () { if (fn.closest('.f').classList.contains('err')) showErr(fn, 'fnErr', !fn.value.trim()); });
    fp.addEventListener('input', function () { if (fp.closest('.f').classList.contains('err')) showErr(fp, 'fpErr', fp.value.replace(/\D/g, '').length < 7); });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = fn.value.trim(), digits = fp.value.replace(/\D/g, '');
      var badName = showErr(fn, 'fnErr', !name);
      var badPhone = showErr(fp, 'fpErr', digits.length < 7 || digits.length > 15);
      if (badName || badPhone) { (badName ? fn : fp).focus(); return; }

      var v = want();
      var phone = /^\s*(\+|00)/.test(fp.value) ? '+' + digits.replace(/^00/, '') : '+971 ' + digits.replace(/^0+/, '');
      var machine = v === 'rent' ? fm.value : fmt.value.trim();
      var lines = [
        'Hi Cherry Pickers Equipment, ' + (v === 'rent' ? "I'd like a rental quote." : v === 'buy' ? "I'd like to buy a machine." : 'I need a service / repair.'),
        'Name: ' + name,
        'Phone: ' + phone
      ];
      if (machine) lines.push((v === 'rent' ? 'Machine or height: ' : v === 'buy' ? 'Machine: ' : 'My machine: ') + machine);
      lines.push((v === 'buy' ? 'Delivery to: ' : 'Emirate: ') + fe.value);
      if (v !== 'buy' && fd.value) lines.push('Start date: ' + fd.value);
      if (fmsg.value.trim()) lines.push('Details: ' + fmsg.value.trim());

      // TODO(backend): send the lead to the real form handler here (e.g. a WordPress form plugin or an email
      // endpoint), routed to Rental & Maintenance LLC (rent / service) or Equipment LLC (buy). Show the thank-you
      // message on success and keep the WhatsApp hand-off below only as a fallback.
      var url = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(lines.join('\n'));
      done.textContent = 'Thanks, ' + name + ' – opening WhatsApp with your enquiry. Just press send. ';
      var a = document.createElement('a');
      a.href = url; a.target = '_blank'; a.rel = 'noopener';
      a.textContent = "WhatsApp didn't open? Tap here.";
      done.appendChild(a);
      var w = window.open(url, '_blank');
      if (w) { try { w.opener = null; } catch (err) { /* ignore */ } } else { window.location.href = url; }
    });
  })();
})();
