"""Builds the Cherry Pickers Equipment HTML mockups.
Partials live in ./pages; shared header, footer, icons and machine cards are defined here.
Output: /home/claude/cpe-mockups/*.html
"""
import re
from pathlib import Path

SRC = Path(__file__).parent / "pages"
OUT = Path(__file__).resolve().parent.parent

PHONE = "+971 56 101 8428"
PHONE_LINK = "tel:+971561018428"
WA_LINK = "https://wa.me/971561018428"
ADDRESS = "Saih Shuaib 4, Dubai Industrial City, Dubai, UAE"

# ---------------------------------------------------------------- icons
_S = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>'
ICONS = {
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 6L2 7"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "wrench": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9z"/>',
    "truck": '<path d="M1 3h15v13H1zM16 8h4l3 3v5h-7z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>',
    "building": '<rect x="4" y="2" width="16" height="20" rx="1"/><path d="M9 22v-4h6v4M8 6h.01M12 6h.01M16 6h.01M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01"/>',
    "warehouse": '<path d="M22 8.4V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8.4a2 2 0 0 1 1.2-1.8l8-3.2a2 2 0 0 1 1.6 0l8 3.2A2 2 0 0 1 22 8.4z"/><path d="M6 18h12M6 14h12M6 22V10h12v12"/>',
    "factory": '<path d="M2 20V8l6 4V8l6 4V4h8v16z"/><path d="M17 16h1M12 16h1M7 16h1"/>',
    "plane": '<path d="M17.8 19.2L16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "hardhat": '<path d="M2 18h20v2H2zM4 18v-3a8 8 0 0 1 16 0v3"/><path d="M10 7V5h4v2"/>',
    "drop": '<path d="M12 2s6 7 6 12a6 6 0 0 1-12 0c0-5 6-12 6-12z"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>',
    "tag": '<path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L2 12V2h10l8.6 8.6a2 2 0 0 1 0 2.8z"/><circle cx="7" cy="7" r="1.5"/>',
    "lift": '<path d="M3 20h10M5 20v-3h6v3M8 17l8-9M16 8l3 2M17 4h5v5h-5z"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 22a8 8 0 0 1 16 0"/>',
    "filter": '<path d="M22 3H2l8 9.5V19l4 2v-8.5z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M12 18v-6M9 15l3 3 3-3"/>',
    "quote": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
    "fb": '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
    "ig": '<rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5h.01"/>',
    "li": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/>',
    "yt": '<path d="M22.5 6.4a2.8 2.8 0 0 0-2-2C18.9 4 12 4 12 4s-6.9 0-8.5.4a2.8 2.8 0 0 0-2 2A29 29 0 0 0 1 12a29 29 0 0 0 .5 5.6 2.8 2.8 0 0 0 2 2c1.6.4 8.5.4 8.5.4s6.9 0 8.5-.4a2.8 2.8 0 0 0 2-2A29 29 0 0 0 23 12a29 29 0 0 0-.5-5.6z"/><path d="M9.8 15.5l5.7-3.5-5.7-3.5z"/>',
    "tt": '<path d="M9 12a4 4 0 1 0 4 4V2h3a5 5 0 0 0 5 5"/>',
    "pinterest": '<circle cx="12" cy="12" r="10"/><path d="M8 21l4-10"/><path d="M10.6 15c.5.8 1.4 1.3 2.6 1.3 2.7 0 4.6-2.4 4.6-5.3a5.8 5.8 0 0 0-11.6 0c0 1.1.3 2 .8 2.7"/>',
    "ruler":'<path d="M21.3 8.7l-6-6a1 1 0 0 0-1.4 0L2.7 13.9a1 1 0 0 0 0 1.4l6 6a1 1 0 0 0 1.4 0L21.3 10.1a1 1 0 0 0 0-1.4zM7.5 10.5l2 2M10.5 7.5l2 2M13.5 4.5l2 2M4.5 13.5l2 2"/>',
    "box": '<path d="M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7z"/><path d="M3.3 7L12 12l8.7-5M12 22V12"/>',
}
WA_SVG = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.3-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.8 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7a2.8 2.8 0 0 0 1.8-1.3 2.3 2.3 0 0 0 .2-1.3c-.1-.1-.2-.2-.4-.3z"/></svg>'


from PIL import Image as _PIL
IMG_DIR = OUT / "assets" / "img"


def media(name, alt, cls="ratio-4-3", eager=False, label=""):
    """Image inside a fixed-ratio box (no layout shift). eager=True for the LCP image only."""
    f = IMG_DIR / f"{name}.webp"
    w, h = _PIL.open(f).size
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    lab = f' data-label="{label}"' if label else ""
    return (f'<div class="media {cls}"{lab}><img src="assets/img/{name}.webp" alt="{alt}" '
            f'width="{w}" height="{h}" {load} decoding="async"></div>')


def icon(name):
    if name == "wa":
        return WA_SVG
    return _S.format(ICONS[name])


# ---------------------------------------------------------------- sample machines (replace with real fleet)
RENTAL = {
    # key: (model, type, image, working height, capacity, power, status, fit)
    "gs1930": ("Genie GS-1930", "Electric Scissor Lift", "r-gs1930", "7.79 m", "227 kg", "Electric", "ok", ""),
    "gs1932": ("Genie GS-1932", "Electric Scissor Lift", "r-gs1932", "7.81 m", "227 kg", "Electric", "ok", ""),
    "gs2646": ("Genie GS-2646", "Electric Scissor Lift", "r-gs2646", "9.9 m", "454 kg", "Electric", "busy", ""),
    "gs3246": ("Genie GS-3246", "Electric Scissor Lift", "r-gs3246", "11.75 m", "318 kg", "Electric", "ok", ""),
    "dingli1412": ("Dingli 1412HD", "Electric Scissor Lift", "r-dingli1412", "13.8 m", "320 kg", "Electric", "ok", ""),
    "m4069le": ("JLG M4069LE", "Electric Scissor Lift", "r-m4069le", "14.19 m", "362 kg", "Electric", "ok", ""),
    "dingli1612": ("Dingli 1612HD", "Electric Scissor Lift", "r-dingli1612", "15.7 m", "250 kg", "Electric", "ok", ""),
    "gs4390": ("Genie GS-4390 RT", "Rough Terrain Scissor Lift", "r-gs4390rt", "15.11 m", "680 kg", "Diesel", "ok", ""),
    "gs5390": ("Genie GS-5390 RT", "Rough Terrain Scissor Lift", "r-gs5390", "18.15 m", "680 kg", "Diesel", "ok", "contain"),
    "ab38e": ("Snorkel AB38E", "Electric Boom Lift", "r-ab38e", "13.5 m", "215 kg", "Electric", "ok", ""),
    "e450aj": ("JLG E450AJ", "Electric Boom Lift", "r-e450aj", "15.7 m", "227 kg", "Electric", "ok", ""),
    "450aj": ("JLG 450AJ", "Articulated Boom Lift", "r-450aj", "15.72 m", "250 kg", "Diesel", "ok", ""),
    "z4525": ("Genie Z-45/25J", "Articulated Boom Lift", "r-z4525j", "15.94 m", "227 kg", "Diesel", "ok", "contain"),
    "600aj": ("JLG 600AJ", "Articulated Boom Lift", "r-600aj", "20.47 m", "227 kg", "Diesel", "busy", ""),
    "s45": ("Genie S-45", "Telescopic Boom Lift", "r-s45", "15.7 m", "227 kg", "Diesel", "ok", ""),
    "s65": ("Genie S-65", "Telescopic Boom Lift", "r-s65", "21.8 m", "227 kg", "Diesel", "ok", ""),
    "860sj": ("JLG 860SJ", "Telescopic Boom Lift", "r-860sj", "28.21 m", "340 kg", "Diesel", "ok", ""),
}

SALE = {
    # key: (year, model, type, image or None, origin, working height, sold)
    "600aj": ("2010", "JLG 600AJ", "Articulated Boom Lift", "s-600aj-1", "Australia", "20.5 m", False),
    "1350": ("2009", "JLG 1350SJP", "Telescopic Boom Lift", "s-1350sjp", "Hong Kong", "43.1 m", False),
    "1200": ("2008", "JLG 1200SJP", "Telescopic Boom Lift", "s-1200sjp", "Denmark", "38.6 m", False),
    "860": ("2011", "JLG 860SJ", "Telescopic Boom Lift", "s-860sj", "Australia", "28.2 m", False),
    "e450": ("2018", "JLG E450AJ", "Electric Articulated Boom", "s-e450aj", "Singapore", "15.7 m", False),
    # sold records (from your Sold page) – photo is a model photo, not the sold unit
    "sold860": ("2017", "JLG 860SJ", "Telescopic Boom Lift", "r-860sj", "Hong Kong", "28.2 m", "Vietnam · Dec 2025"),
    "soldS65": ("2016", "Genie S-65", "Telescopic Boom Lift", "r-s65", "USA", "21.8 m", "India · Dec 2025"),
    "sold660": ("2016", "JLG 660SJ", "Telescopic Boom Lift", None, "USA", "22.1 m", "India · Dec 2025"),
}

STATUS = {"ok": '<span class="badge badge--ok">Available</span>',
          "busy": '<span class="badge badge--busy">On hire – ask for date</span>'}


def rental_card(key):
    m, t, img, h, cap, pw, st, fit = RENTAL[key]
    return f'''<article class="machine-card">
  <div class="card-top-badges">{STATUS[st]}</div>
  {media(img + "-sm", f"{m} {t.lower()} for rent in Dubai", "ratio-4-3 " + fit)}
  <div class="machine-card-body">
    <div>
      <h3><a href="rental-detail.html">{m}</a></h3>
      <div class="machine-type">{t}</div>
    </div>
    <div class="spec-mini">
      <div><strong>{h}</strong>Working height</div>
      <div><strong>{cap}</strong>Capacity</div>
      <div><strong>{pw}</strong>Power</div>
    </div>
    <div class="machine-actions">
      <a class="btn btn--ghost btn--sm" href="rental-detail.html" style="justify-content:center">Details</a>
      <a class="btn btn--red btn--sm" href="contact.html#enquiry" style="justify-content:center">Get Quote</a>
    </div>
  </div>
</article>'''


def sale_card(key):
    y, m, t, img, origin, h, sold = SALE[key]
    ribbon = '<div class="ribbon-sold">SOLD</div>' if sold else ""
    cls = "machine-card is-sold" if sold else "machine-card"
    if img:
        pic = media(img + "-sm", f"{m} {t.lower()}", "ratio-4-3", label="Model photo" if sold else "")
    else:
        pic = f'<div class="ph ratio-4-3" data-label="Photo: {y} {m}"></div>'
    price = f'<div class="price">Sold <small>Exported to {sold}</small></div>' if sold else '<div class="price">Contact for price <small>UAE &amp; export enquiries</small></div>'
    btn2 = '<a class="btn btn--navy btn--sm" href="equipment-for-sale.html" style="justify-content:center">Similar</a>' if sold else '<a class="btn btn--red btn--sm" href="contact.html#enquiry" style="justify-content:center">Enquire</a>'
    return f'''<article class="{cls}">
  {ribbon}
  {pic}
  <div class="machine-card-body">
    <div>
      <h3><a href="sale-detail.html">{y} {m}</a></h3>
      <div class="machine-type">{t}</div>
    </div>
    <div class="spec-mini">
      <div><strong>{y}</strong>Year</div>
      <div><strong>{origin}</strong>Origin</div>
      <div><strong>{h}</strong>Working ht.</div>
    </div>
    {price}
    <div class="machine-actions">
      <a class="btn btn--ghost btn--sm" href="sale-detail.html" style="justify-content:center">Details</a>
      {btn2}
    </div>
  </div>
</article>'''


# ---------------------------------------------------------------- shared blocks
CATS = [
    ("Electric Scissor Lifts", "rental-category.html"),
    ("Rough Terrain Scissor Lifts", "rental-category.html"),
    ("Electric Boom Lifts", "rental-category.html"),
    ("Articulated Boom Lifts", "rental-category.html"),
    ("Telescopic Boom Lifts", "rental-category.html"),
]


def header(active):
    def cur(name):
        return ' aria-current="page"' if name == active else ""
    cat_links = "".join(f'<li><a href="{u}">{n}</a></li>' for n, u in CATS)
    return f'''<div class="mock-note">UI mockup for review · real photos and machines from your website · grey boxes = photos still needed</div>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="index.html">
      <img src="assets/img/logo.webp" alt="Cherry Pickers Equipment – The Right Pick for Every Height" width="1024" height="340" class="logo-img">
    </a>
    <nav class="main-nav" aria-label="Main">
      <ul>
        <li class="has-drop"><a href="rental.html"{cur("rental")}>Rental</a>
          <ul class="drop">{cat_links}<li><a href="rental.html"><strong>All rental machines →</strong></a></li></ul>
        </li>
        <li><a href="equipment-for-sale.html"{cur("sale")}>Equipment for Sale</a></li>
        <li class="has-drop"><a href="services.html"{cur("services")}>Services</a>
          <ul class="drop">
            <li><a href="rental.html">Equipment Rental<small>Daily, weekly, monthly, long-term</small></a></li>
            <li><a href="maintenance-repair.html">Maintenance &amp; Repair<small>AMC, servicing, breakdown repair</small></a></li>
            <li><a href="equipment-for-sale.html">Equipment Sales<small>Used machines, UAE &amp; export</small></a></li>
          </ul>
        </li>
        <li><a href="about.html"{cur("about")}>About</a></li>
        <li><a href="blog.html"{cur("blog")}>Blog</a></li>
        <li><a href="contact.html"{cur("contact")}>Contact</a></li>
      </ul>
    </nav>
    <div class="header-actions">
      <a class="header-phone" href="{PHONE_LINK}">{icon("phone")}<span>{PHONE}</span></a>
      <a class="icon-btn" href="{WA_LINK}" aria-label="WhatsApp">{WA_SVG}</a>
      <a class="btn btn--red btn--sm" href="contact.html#enquiry">Get a Quote</a>
    </div>
    <button class="menu-toggle" aria-label="Open menu" aria-expanded="false"><span></span></button>
  </div>
</header>'''


def breadcrumbs(items):
    if not items:
        return ""
    lis = ['<li><a href="index.html">Home</a></li>']
    for i, (n, u) in enumerate(items):
        if i == len(items) - 1:
            lis.append(f'<li aria-current="page">{n}</li>')
        else:
            lis.append(f'<li><a href="{u}">{n}</a></li>')
    return f'<nav class="breadcrumbs wrap" aria-label="Breadcrumb"><ol>{"".join(lis)}</ol></nav>'


def cta(title="Need a machine? Get a quote today.",
        text="Tell us the working height, the job and the site location. We'll suggest the right machine and send a quote."):
    return f'''<section class="cta-band" id="enquiry-strip">
  <div class="wrap cta-grid">
    <div>
      <span class="eyebrow">Talk to our team</span>
      <h2>{title}</h2>
      <p>{text}</p>
      <div class="cta-contacts">
        <a href="{PHONE_LINK}">{icon("phone")} {PHONE}</a>
        <a href="{WA_LINK}">{WA_SVG.replace('<svg', '<svg style="color:#3ddc84"')} WhatsApp us</a>
        <span class="small">{icon("clock").replace('<svg', '<svg style="width:18px;height:18px;display:inline;vertical-align:-3px;color:#ff5a45"')} Mon–Sat 9:00–19:00 · Sunday closed</span>
      </div>
    </div>
    {quick_form()}
  </div>
</section>'''


def quick_form(title="Quick enquiry"):
    return f'''<form class="form-card" data-mock>
      <h3>{title}</h3>
      <p class="hint">We reply during working hours. Only name and phone are required.</p>
      <div class="form-grid">
        <div class="field"><label>Name <span class="req">*</span></label><input required placeholder="Your name"></div>
        <div class="field"><label>Phone <span class="req">*</span></label><input required placeholder="+971"></div>
        <div class="field"><label>Machine needed</label><select><option>Not sure – advise me</option><option>Electric scissor lift</option><option>Rough terrain scissor lift</option><option>Electric boom lift</option><option>Articulated boom lift</option><option>Telescopic boom lift</option></select></div>
        <div class="field"><label>Emirate</label><select><option>Dubai</option><option>Abu Dhabi</option><option>Sharjah</option><option>Ajman</option><option>Ras Al Khaimah</option><option>Fujairah</option><option>Umm Al Quwain</option></select></div>
        <div class="full"><button class="btn btn--red btn--block" type="submit">Send enquiry</button></div>
      </div>
      <div class="form-ok">Thanks – this is a mockup, nothing was sent.</div>
    </form>'''


def footer():
    cat_links = "".join(f'<li><a href="{u}">{n}</a></li>' for n, u in CATS)
    return f'''<footer class="site-footer">
  <div class="wrap footer-grid">
    <div class="footer-about">
      <a class="logo logo--footer" href="index.html"><img src="assets/img/logo.webp" alt="Cherry Pickers Equipment" width="1024" height="340" loading="lazy" class="logo-img"></a>
      <p>Boom lift and scissor lift rental across all seven UAE emirates, with maintenance and used equipment sales.</p>
      <div class="social">
        <a href="#" aria-label="Facebook">{icon("fb")}</a><a href="#" aria-label="Instagram">{icon("ig")}</a>
        <a href="https://www.linkedin.com/company/cherry-pickers-equipment/" aria-label="LinkedIn">{icon("li")}</a><a href="#" aria-label="YouTube">{icon("yt")}</a>
      </div>
    </div>
    <div>
      <h3>Rental</h3>
      <ul>{cat_links}<li><a href="rental.html">All rental machines</a></li></ul>
    </div>
    <div>
      <h3>Company</h3>
      <ul>
        <li><a href="about.html">About us</a></li>
        <li><a href="services.html">Services</a></li>
        <li><a href="maintenance-repair.html">Maintenance &amp; Repair</a></li>
        <li><a href="equipment-for-sale.html">Equipment for Sale</a></li>
        <li><a href="blog.html">Blog</a></li>
        <li><a href="contact.html">Contact</a></li>
      </ul>
    </div>
    <div>
      <h3>Contact</h3>
      <ul class="footer-contact">
        <li>{icon("pin")}<span>{ADDRESS}</span></li>
        <li>{icon("phone")}<a href="{PHONE_LINK}">{PHONE}</a></li>
        <li>{icon("mail")}<span>[your email]</span></li>
        <li>{icon("clock")}<span>Mon–Sat 9:00–19:00<br>Sunday closed</span></li>
      </ul>
    </div>
  </div>
  <div class="wrap footer-bottom">
    <span>© 2026 Cherry Pickers Equipment. All rights reserved.</span>
    <span><a href="privacy-policy.html">Privacy Policy</a> · <a href="terms-and-conditions.html">Terms &amp; Conditions</a></span>
  </div>
</footer>
<nav class="mobile-bar" aria-label="Quick contact">
  <a href="{PHONE_LINK}">{icon("phone")}Call</a>
  <a class="wa" href="{WA_LINK}">{WA_SVG}WhatsApp</a>
  <a class="quote" href="contact.html#enquiry">{icon("quote")}Get Quote</a>
</nav>'''


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@600;700;800&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
{header}
<main>
{crumbs}
{body}
</main>
{footer}
<script src="assets/js/main.js" defer></script>
</body>
</html>
"""

# file, partial, title, description, active nav, breadcrumbs
PAGES = [
    ("index.html", "home", "Boom Lift & Scissor Lift Rental in Dubai & UAE | Cherry Pickers Equipment",
     "Rent boom lifts and scissor lifts across all 7 UAE emirates, book maintenance, or buy used access equipment.", "home", []),
    ("about.html", "about", "About Us | Cherry Pickers Equipment, Dubai",
     "Who we are: access equipment rental, maintenance and used machine sales from Dubai Industrial City.", "about",
     [("About", "")]),
    ("rental.html", "rental", "Access Equipment for Rent in Dubai & UAE | Cherry Pickers Equipment",
     "All boom lifts and scissor lifts for rent, with working height, capacity and availability.", "rental",
     [("Rental", "")]),
    ("rental-category.html", "category", "Electric Scissor Lift Rental in Dubai & UAE | Cherry Pickers Equipment",
     "Electric scissor lifts for rent in Dubai and across the UAE, 7.8 m to 15.7 m working height.", "rental",
     [("Rental", "rental.html"), ("Electric Scissor Lifts", "")]),
    ("rental-detail.html", "rental-detail", "Genie GS-3246 Electric Scissor Lift for Rent in Dubai | Cherry Pickers Equipment",
     "Rent the Genie GS-3246 electric scissor lift in Dubai: 11.75 m working height, 318 kg capacity.", "rental",
     [("Rental", "rental.html"), ("Electric Scissor Lifts", "rental-category.html"), ("Genie GS-3246", "")]),
    ("equipment-for-sale.html", "sale", "Used Access Equipment for Sale – UAE & Export | Cherry Pickers Equipment",
     "Used boom lifts and scissor lifts for sale in the UAE and for export, with year, hours and photos.", "sale",
     [("Equipment for Sale", "")]),
    ("sale-detail.html", "sale-detail", "Used 2010 JLG 600AJ Articulated Boom Lift for Sale | Cherry Pickers Equipment",
     "Used 2010 JLG 600AJ articulated boom lift for sale: 20.5 m working height, Australian origin.", "sale",
     [("Equipment for Sale", "equipment-for-sale.html"), ("2010 JLG 600AJ", "")]),
    ("services.html", "services", "Access Equipment Services in UAE | Cherry Pickers Equipment",
     "Equipment rental, maintenance and repair, and used machine sales across the UAE.", "services",
     [("Services", "")]),
    ("maintenance-repair.html", "maintenance", "MEWP Maintenance & Repair in Dubai & UAE | Cherry Pickers Equipment",
     "Maintenance contracts (AMC), servicing and breakdown repair for boom lifts and scissor lifts.", "services",
     [("Services", "services.html"), ("Maintenance & Repair", "")]),
    ("blog.html", "blog", "Blog – Access Equipment Guides & Tips | Cherry Pickers Equipment",
     "Guides on choosing, renting and operating boom lifts and scissor lifts in the UAE.", "blog",
     [("Blog", "")]),
    ("blog-detail.html", "blog-detail", "Boom Lift vs Scissor Lift: How to Choose | Cherry Pickers Equipment",
     "How to choose between a boom lift and a scissor lift for your UAE project.", "blog",
     [("Blog", "blog.html"), ("Boom Lift vs Scissor Lift", "")]),
    ("contact.html", "contact", "Contact Us | Cherry Pickers Equipment, Dubai Industrial City",
     "Call, WhatsApp or send an enquiry for access equipment rental, maintenance or sales.", "contact",
     [("Contact", "")]),
    ("privacy-policy.html", "legal", "Privacy Policy | Cherry Pickers Equipment",
     "How Cherry Pickers Equipment collects and uses personal information.", "",
     [("Privacy Policy", "")]),
    ("terms-and-conditions.html", "terms", "Terms & Conditions | Cherry Pickers Equipment",
     "Rental, maintenance and sales terms of Cherry Pickers Equipment.", "",
     [("Terms & Conditions", "")]),
]


def render_tokens(html):
    html = re.sub(r"\{\{icon:(\w+)\}\}", lambda m: icon(m.group(1)), html)
    def _media(m):
        parts = m.group(1).split("|")
        name, alt = parts[0], parts[1]
        cls = parts[2] if len(parts) > 2 and parts[2] else "ratio-4-3"
        eager = len(parts) > 3 and parts[3] == "eager"
        label = parts[4] if len(parts) > 4 else ""
        return media(name, alt, cls, eager, label)
    html = re.sub(r"\{\{media:([^}]*)\}\}", _media, html)
    html = re.sub(r"\{\{rcard:(\w+)\}\}", lambda m: rental_card(m.group(1)), html)
    html = re.sub(r"\{\{scard:(\w+)\}\}", lambda m: sale_card(m.group(1)), html)
    html = re.sub(r"\{\{form(?::([^}]*))?\}\}", lambda m: quick_form(m.group(1) or "Quick enquiry"), html)

    def _cta(m):
        if m.group(1):
            t, x = m.group(1).split("|", 1)
            return cta(t, x)
        return cta()
    html = re.sub(r"\{\{cta(?::([^}]*))?\}\}", _cta, html)
    html = html.replace("{{PHONE}}", PHONE).replace("{{PHONE_LINK}}", PHONE_LINK).replace("{{WA_LINK}}", WA_LINK).replace("{{ADDRESS}}", ADDRESS)
    return html


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    built = []
    for fname, part, title, desc, active, crumbs in PAGES:
        p = SRC / f"{part}.html"
        if not p.exists():
            continue
        body = render_tokens(p.read_text(encoding="utf-8"))
        html = PAGE.format(title=title, desc=desc, header=header(active),
                           crumbs=breadcrumbs([(n, u) for n, u in crumbs]),
                           body=body, footer=footer())
        (OUT / fname).write_text(html, encoding="utf-8")
        built.append(fname)
    print("Built:", ", ".join(built))


if __name__ == "__main__":
    build()
