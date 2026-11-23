/* Cherry Pickers Equipment – site-wide quote popup + shared quote forms. No libraries, no build step.
   Markup: assets/partials/quote-modal.html (from _source/quote.py) · styles: assets/css/quote-modal.css
   Triggers: any element with data-quote [data-type="rental|sale|service"] [data-machine] [data-category] [data-sold]. */
const QUOTE_CONFIG = {
  endpoint: null,            // later: WordPress form handler URL; null = mockup mode
  whatsappNumber: '971561018428',
  phoneDisplay: '+971 56 101 8428',
  emailTo: 'info@cherrypickersglobal.com'
};

(function () {
  var C = QUOTE_CONFIG, d = document, root = d.documentElement;
  var dlg = d.getElementById('quote-modal'), popup = dlg && dlg.querySelector('form');
  var PH = { rental: 'Working height, indoor/outdoor, site location…', sale: 'Year range, working height, quantity, destination…',
    service: 'Brand, model, the problem and where the machine is…' };
  var ATTR = ['gclid', 'gbraid', 'wbraid', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'];
  var SPIDER = /spider/i, state = {}, opener = null, lastKey = null, done = false;

  function track(o) { window.dataLayer = window.dataLayer || []; window.dataLayer.push(o); }
  function pad(n) { return ('0' + n).slice(-2); }
  function today() { var t = new Date(); return t.getFullYear() + '-' + pad(t.getMonth() + 1) + '-' + pad(t.getDate()); } // local date, not UTC

  // Ad attribution: read from the URL, kept for the session, sent with every enquiry as hidden fields
  var attr = {};
  try { attr = JSON.parse(sessionStorage.getItem('cpe_attr')) || {}; } catch (e) { attr = {}; }
  (function () {
    var p = new URLSearchParams(location.search), got = false;
    ATTR.forEach(function (k) { var v = p.get(k); if (v) { attr[k] = v.slice(0, 200); got = true; } });
    if (got) { try { sessionStorage.setItem('cpe_attr', JSON.stringify(attr)); } catch (e) { /* storage blocked */ } }
  })();

  function field(f, name) { return f.querySelector('[name="' + name + '"]:not([type=radio])'); }
  function hidden(f, name, value) {
    var i = f.querySelector('input[type=hidden][name="' + name + '"]');
    if (!i) { i = d.createElement('input'); i.type = 'hidden'; i.name = name; f.appendChild(i); }
    i.value = value;
  }
  function getType(f) {
    var r = f.querySelector('input[name=enquiry_type]:checked') || f.querySelector('input[name=enquiry_type]');
    return r ? r.value : 'rental';
  }
  function machineOf(f) {
    var n = ['machine', 'machine_model', 'service_machine', 'machine_category'];
    for (var i = 0; i < n.length; i++) { var c = field(f, n[i]); if (c && !c.disabled && c.value.trim()) return c.value.trim(); }
    return '';
  }

  // Show the field groups for one enquiry type; the others get hidden + disabled (not required, not submitted)
  function setType(f, type) {
    type = PH[type] ? type : 'rental';
    var r = f.querySelector('input[name=enquiry_type][value="' + type + '"]');
    if (r) r.checked = true;
    f.querySelectorAll('[data-for]').forEach(function (g) {
      var on = g.getAttribute('data-for').split(' ').indexOf(type) > -1;
      g.hidden = !on;
      g.querySelectorAll('input,select,textarea').forEach(function (c) { c.disabled = !on; if (!on) clearErr(c); });
    });
    var det = f.querySelector('[data-qf-details]');
    if (det) det.placeholder = PH[type];
  }

  function prefill(f, s) {
    setType(f, s.type);
    var cat = field(f, 'machine_category');
    if (cat) [].forEach.call(cat.options, function (o) { o.selected = !!s.category && o.text.toLowerCase() === s.category.toLowerCase(); });
    var mod = field(f, 'machine_model');
    if (mod && s.type === 'sale') mod.value = s.machine;
    var lab = f.querySelector('[data-qf-model-label]');
    if (lab) lab.textContent = s.sold ? 'Machine wanted' : 'Machine or model';
    hidden(f, 'machine', s.machine);
  }

  // ---------- validation ----------
  function clearErr(c) {
    if (!c || !c.getAttribute || c.getAttribute('aria-invalid') !== 'true') return;
    c.removeAttribute('aria-invalid');
    var e = d.getElementById(c.id + '-err');
    if (e) e.parentNode.removeChild(e);
    var db = (c.getAttribute('aria-describedby') || '').replace(c.id + '-err', '').trim();
    if (db) c.setAttribute('aria-describedby', db); else c.removeAttribute('aria-describedby');
  }
  function setErr(c, msg) {
    clearErr(c);
    var e = d.createElement('p');
    e.className = 'qf-err'; e.id = c.id + '-err'; e.textContent = msg;
    c.parentNode.insertBefore(e, c.nextSibling);
    c.setAttribute('aria-invalid', 'true');
    c.setAttribute('aria-describedby', ((c.getAttribute('aria-describedby') || '') + ' ' + e.id).trim());
  }
  function validate(f) {
    var first = null;
    f.querySelectorAll('input,select,textarea').forEach(function (c) {
      if (c.disabled || c.type === 'hidden' || c.name === 'website' || !c.id) return;
      var v = c.value.trim(), msg = '';
      if (c.type === 'tel' && (v || c.required)) {
        if (!v) msg = 'Please enter a phone number we can call or WhatsApp.';
        else if (!/^\d{7,15}$/.test(v.replace(/[\s+\-()]/g, ''))) msg = 'Please enter a valid phone number (at least 7 digits).';
      } else if (c.required && !v) msg = c.name === 'name' ? 'Please enter your name.' : 'Please fill in this field.';
      else if (c.type === 'email' && v && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) msg = 'Please enter a valid email address.';
      if (msg) { setErr(c, msg); first = first || c; } else clearErr(c);
    });
    return first;
  }

  // ---------- WhatsApp + titles ----------
  function waText(s) {
    var m = s.machine;
    if (SPIDER.test(s.category || '')) return "Hi, I'd like to register interest in a spider lift.";
    if (s.sold && m) return "Hi, I'm looking for a machine like the " + m + '.';
    if (s.type === 'sale') return m ? "Hi, I'm interested in buying the " + m + '.' : "Hi, I'd like to buy a machine.";
    if (s.type === 'service') return 'Hi, I need a service for my machine.';
    if (m) return "Hi, I'd like a quote for the " + m + ' (rental).';
    if (s.category) return "Hi, I'd like a quote for a " + s.category.toLowerCase() + ' (rental).';
    return "Hi, I'd like a quote.";
  }
  function waUrl(s) { return 'https://wa.me/' + C.whatsappNumber + '?text=' + encodeURIComponent(waText(s)); }
  function title(s) {
    if (SPIDER.test(s.category)) return 'Register interest: spider lift';
    if (!s.machine) return 'Get a quote';
    if (s.sold) return 'Find me a machine like: ' + s.machine;
    return (s.type === 'sale' ? 'Enquire about this machine: ' : 'Get a quote: ') + s.machine;
  }
  function updateWa() { dlg.querySelectorAll('[data-qm-wa]').forEach(function (a) { a.href = waUrl(state); }); }

  // ---------- popup ----------
  function lock() {
    var sw = window.innerWidth - root.clientWidth;
    root.style.overflow = 'hidden';
    if (sw > 0) root.style.paddingRight = sw + 'px';
  }
  function reset() {
    done = false;
    popup.reset();
    popup.hidden = false;
    var ok = dlg.querySelector('.qf-success');
    if (ok) ok.parentNode.removeChild(ok);
    popup.querySelectorAll('[aria-invalid=true]').forEach(clearErr);
    status(popup, '');
  }
  function open(s, from) {
    if (!dlg) return false;
    s = { general: !PH[s.type], type: PH[s.type] ? s.type : 'rental', machine: s.machine || '', category: s.category || '', sold: !!s.sold };
    var key = [s.general ? '' : s.type, s.machine, s.category, s.sold].join('|');
    if (key !== lastKey || done) {   // new machine (or after a sent enquiry): start fresh; same machine: keep what was typed
      reset();
      prefill(popup, s);
      popup.querySelector('[data-qf-toggle]').hidden = !!(s.machine || s.category);
      lastKey = key;
    }
    state = s;
    state.type = getType(popup);
    popup.querySelectorAll('[data-qf-date]').forEach(function (i) { i.min = today(); });
    d.getElementById('qm-title').textContent = title(s);
    updateWa();
    opener = from || null;
    lock();
    if (!dlg.open) dlg.showModal();
    popup.querySelector('[name=name]').focus();
    return true;
  }

  if (dlg) {
    dlg.addEventListener('close', function () {
      root.style.overflow = ''; root.style.paddingRight = '';
      var t = opener;
      if (!t || !t.isConnected || !t.getClientRects().length) t = d.getElementById('burger') || d.querySelector('.menu-toggle');
      if (t && t.getClientRects().length) t.focus();
      opener = null;
    });
    // backdrop click: press and release both outside the dialog box
    var outside = function (e) {
      if (e.target !== dlg) return false;
      var r = dlg.getBoundingClientRect();
      return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    }, downOut = false;
    dlg.addEventListener('pointerdown', function (e) { downOut = outside(e); });
    dlg.addEventListener('click', function (e) { if (downOut && outside(e)) dlg.close(); downOut = false; });
  }

  // One delegated listener: quote triggers, popup close buttons, popup WhatsApp clicks
  d.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-quote],[data-qm-close],[data-qm-wa]');
    if (!t) return;
    if (t.hasAttribute('data-qm-close')) { if (dlg) dlg.close(); return; }
    if (t.hasAttribute('data-qm-wa')) { track({ event: 'whatsapp_click', location: 'quote_popup', machine: state.machine || '' }); return; }
    if (!dlg || e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return; // no popup (Contact page): the link scrolls to the form
    e.preventDefault();
    open({ type: t.getAttribute('data-type'), machine: t.getAttribute('data-machine'),
      category: t.getAttribute('data-category'), sold: t.hasAttribute('data-sold') }, t);
  });

  // ---------- submit ----------
  function status(f, html) { var s = f.querySelector('.qf-status'); if (s) { s.hidden = !html; s.innerHTML = html; } }
  function busy(f, on) {
    var b = f.querySelector('[type=submit]');
    if (!b) return;
    if (!b.getAttribute('data-label')) b.setAttribute('data-label', b.textContent);
    b.disabled = on;
    b.textContent = on ? 'Sending…' : b.getAttribute('data-label');
  }
  function send(f, spam) {
    if (spam || !C.endpoint) return new Promise(function (r) { setTimeout(r, 600); });  // mockup mode
    return fetch(C.endpoint, { method: 'POST', body: new FormData(f), headers: { Accept: 'application/json' } })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); });
  }
  function success(f, s, inPopup) {
    var ic = d.querySelector('a[href*="wa.me"] svg'), box = d.createElement('div');
    box.className = 'qf-success';
    box.innerHTML = '<h3 tabindex="-1">Thanks, we’ve got your enquiry.</h3><p>We’ll call or WhatsApp you shortly.</p>' +
      '<div class="qf-actions">' + (inPopup ? '<button type="button" class="qf-btn qf-btn--ghost" data-qm-close>Close</button>' : '') +
      '<a class="qf-wa"' + (inPopup ? ' data-qm-wa' : '') + ' href="' + waUrl(s) + '" target="_blank" rel="noopener">' +
      (ic ? ic.outerHTML : '') + '<span>Urgent? WhatsApp us</span></a></div>';
    if (inPopup) { f.hidden = true; dlg.appendChild(box); done = true; } else {
      [].forEach.call(f.children, function (c) { c.hidden = true; });
      f.appendChild(box);
    }
    box.querySelector('h3').focus();
  }

  function bindForm(f) {
    if (f.getAttribute('data-qf-bound')) return;
    f.setAttribute('data-qf-bound', '1');
    var inPopup = f === popup;
    Object.keys(attr).forEach(function (k) { hidden(f, k, attr[k]); });
    f.querySelectorAll('[data-qf-date]').forEach(function (i) { i.min = today(); });
    f.addEventListener('input', function (e) { clearErr(e.target); });
    f.addEventListener('change', function (e) {
      clearErr(e.target);
      if (e.target.name === 'enquiry_type' && e.target.type === 'radio') {
        setType(f, e.target.value);
        if (inPopup) { state.type = e.target.value; updateWa(); }
      }
    });
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      if (f.getAttribute('aria-busy') === 'true') return;
      status(f, '');
      var bad = validate(f);
      if (bad) { bad.focus(); return; }
      hidden(f, 'page_url', location.href);
      hidden(f, 'page_title', d.title);
      var hp = f.querySelector('[name=website]'), spam = !!(hp && hp.value);
      var info = { enquiry_type: getType(f), machine: machineOf(f) };
      var s = inPopup ? state : { type: info.enquiry_type, machine: info.machine };
      f.setAttribute('aria-busy', 'true');
      busy(f, true);
      send(f, spam).then(function () {
        if (!spam) track({ event: 'generate_lead', form_id: inPopup ? 'quote_popup' : 'inline_enquiry', enquiry_type: info.enquiry_type, machine: info.machine });
        success(f, s, inPopup);
      }, function () {
        status(f, 'Couldn’t send. Please try again or <a href="' + waUrl(s) + '" target="_blank" rel="noopener">WhatsApp us</a>.');
      }).then(function () { f.removeAttribute('aria-busy'); busy(f, false); });
    });
  }
  d.querySelectorAll('form[data-quote-form]').forEach(bindForm);

  // ---------- links from ads / other pages: #quote, ?machine=, ?type= (also ?need=rent|buy) ----------
  function fromQuery() {
    var p = new URLSearchParams(location.search), t = (p.get('type') || p.get('need') || '').toLowerCase();
    return { type: { rent: 'rental', rental: 'rental', buy: 'sale', sale: 'sale', service: 'service' }[t] || '',
      machine: (p.get('machine') || '').trim().slice(0, 120), category: (p.get('category') || '').trim().slice(0, 60) };
  }
  var q = fromQuery(), h = location.hash;
  if (dlg && (h === '#quote' || (h === '#enquiry' && !d.getElementById('enquiry')))) open(q, null);
  var pf = d.querySelector('form[data-qf-prefill]');   // Contact page inline form
  if (pf && (q.type || q.machine)) {
    prefill(pf, { type: q.type || 'rental', machine: q.machine, category: q.category });
    var det = field(pf, 'details');
    if (q.machine && q.type !== 'sale' && det && !det.value) det.value = 'Looking for: ' + q.machine;
  }

  window.CPEQuote = { config: C, open: open, bindForm: bindForm, setType: setType, validate: validate, track: track };
})();
