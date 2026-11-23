"""Quote form + popup markup – the single source for every quote form on the site.

Used by build.py for:
  - the popup <dialog id="quote-modal"> (quote_modal) – also written to assets/partials/quote-modal.html
  - inline forms (home, contact, rental/sale detail sidebars) via the {{quotefields:...}} token
  - trigger attributes on buttons (quote_attrs)
Behaviour lives in assets/js/quote-modal.js, styles in assets/css/quote-modal.css.

Field groups carry data-for="rental|sale|service"; JS (CPEQuote.setType) shows the group for the chosen
enquiry type and sets hidden + disabled on the others, so hidden fields are neither required nor submitted.
Every id is prefixed per form (qm- popup, qs- sidebar, qh- home, qc- contact; qe- = shared bottom section in
build.py), so several forms can sit on one page.
"""
from html import escape

from legacy import WA_SVG as _WA_SVG

PHONE = "+971 56 101 8428"
PHONE_LINK = "tel:+971561018428"
WA_NUMBER = "971561018428"

# Rental sub-categories (= build.py CATS[...]["one"].capitalize()), boom types then scissor types. Spider must stay last ([-1]).
CATEGORIES = ["Telescopic boom lift", "Articulated boom lift", "Electric boom lift",
              "Slab electric scissor lift", "Rough terrain electric scissor lift", "Diesel 4x4 scissor lift",
              "Spider lift (coming soon)"]
EMIRATES = ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"]
PERIODS = ["Daily", "Weekly", "Monthly", "Long-term", "Not sure"]
SERVICES = ["AMC – annual maintenance contract", "On-site repair", "Workshop service"]
DETAILS_PH = {
    "rental": "Working height, indoor/outdoor, site location…",
    "sale": "Year range, working height, quantity, destination…",
    "service": "Brand, model, the problem and where the machine is…",
}
TYPE_LABELS = [("rental", "Rent"), ("sale", "Buy"), ("service", "Service")]

WA_SVG = _WA_SVG.replace('aria-hidden="true"', 'aria-hidden="true" focusable="false"')
X_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
         'aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6L6 18"/></svg>')


def esc(v):
    return escape(str(v), quote=True)


def quote_attrs(qtype="", machine="", category="", sold=False):
    """data-* attributes for a trigger link: data-quote [data-type] [data-machine] [data-category] [data-sold]."""
    out = "data-quote"
    for k, v in (("type", qtype), ("machine", machine), ("category", category)):
        if v:
            out += f' data-{k}="{esc(v)}"'
    return out + (" data-sold" if sold else "")


def _opts(items, selected=""):
    return "".join(f'<option{" selected" if o == selected else ""}>{esc(o)}</option>' for o in items)


def _group(types, active, inner, cls="qf-field"):
    """Field wrapper shown only for the given enquiry types. Inactive groups render hidden + disabled (no-JS state)."""
    on = active in types.split()
    dis = "" if on else " disabled"
    return (f'<div class="{cls}" data-for="{types}"{"" if on else " hidden"}>'
            + inner.replace("{dis}", dis) + "</div>")


def quote_fields(p, qtype="rental", machine="", category="", toggle=True, sold=False):
    """All quote fields for one form. p = id prefix ('qm-', 'qs-', ...).
    qtype = initial enquiry type; machine/category pre-fill (machine = specific model, kept in the hidden 'machine' field)."""
    req = ' <span class="qf-req" aria-hidden="true">*</span>'
    radios = "".join(
        f'<label class="qf-seg"><input type="radio" name="enquiry_type" value="{v}"{" checked" if v == qtype else ""}><span>{lab}</span></label>'
        for v, lab in TYPE_LABELS)
    seg = (f'<fieldset class="qf-toggle" data-qf-toggle{"" if toggle else " hidden"}><legend class="qf-legend">I want to</legend>'
           f'<div class="qf-segs">{radios}</div></fieldset>')
    cat_sel = category if category in CATEGORIES else ""
    model_label = "Machine wanted" if sold else "Machine or model"
    rows = [
        f'<div class="qf-field"><label for="{p}name">Name{req}</label>'
        f'<input id="{p}name" name="name" required autocomplete="name"></div>',
        f'<div class="qf-field"><label for="{p}phone">Phone / WhatsApp{req}</label>'
        f'<input id="{p}phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required placeholder="+971 50 123 4567"></div>',
        f'<div class="qf-field"><label for="{p}company">Company</label>'
        f'<input id="{p}company" name="company" autocomplete="organization"></div>',
        f'<div class="qf-field"><label for="{p}email">Email</label>'
        f'<input id="{p}email" name="email" type="email" autocomplete="email"></div>',
        _group("rental", qtype, f'<label for="{p}category">Machine needed</label><select id="{p}category" name="machine_category"{{dis}}>'
               f'<option value="">Not sure – advise me</option>{_opts(CATEGORIES, cat_sel)}</select>'),
        _group("sale", qtype, f'<label for="{p}model" data-qf-model-label>{model_label}</label>'
               f'<input id="{p}model" name="machine_model" value="{esc(machine if qtype == "sale" else "")}" placeholder="e.g. JLG 860SJ"{{dis}}>'),
        _group("service", qtype, f'<label for="{p}service">Service needed</label><select id="{p}service" name="service_needed"{{dis}}>'
               f'{_opts(SERVICES)}</select>'),
        _group("service", qtype, f'<label for="{p}smachine">Machine make / model</label>'
               f'<input id="{p}smachine" name="service_machine" placeholder="e.g. Genie GS-3246"{{dis}}>'),
        _group("rental service", qtype, f'<label for="{p}emirate">Emirate</label><select id="{p}emirate" name="emirate"{{dis}}>{_opts(EMIRATES)}</select>'),
        _group("sale", qtype, f'<label for="{p}country">Country</label>'
               f'<input id="{p}country" name="country" autocomplete="country-name" placeholder="e.g. India"{{dis}}>'),
        _group("rental", qtype, f'<label for="{p}date">Start date</label><input id="{p}date" name="start_date" type="date" data-qf-date{{dis}}>'),
        _group("rental", qtype, f'<label for="{p}period">Rental period</label><select id="{p}period" name="rental_period"{{dis}}>'
               f'<option value="">Choose…</option>{_opts(PERIODS)}</select>'),
        f'<div class="qf-field qf-full"><label for="{p}details">Job details</label>'
        f'<textarea id="{p}details" name="details" rows="3" data-qf-details placeholder="{esc(DETAILS_PH[qtype])}"></textarea></div>',
        _group("rental", qtype, f'<input id="{p}operator" name="operator" type="checkbox" value="yes"{{dis}}>'
               f'<label for="{p}operator">I need an operator <span class="qf-hint">(supplied on request)</span></label>',
               cls="qf-field qf-full qf-check"),
    ]
    hidden = (f'<input type="hidden" name="machine" value="{esc(machine)}">'
              '<input type="hidden" name="page_url" value=""><input type="hidden" name="page_title" value="">'
              f'<div class="qf-hp" aria-hidden="true"><label for="{p}website">Website</label>'
              f'<input id="{p}website" name="website" tabindex="-1" autocomplete="off"></div>')
    return seg + '<div class="qf-grid">' + "".join(rows) + "</div>" + hidden


def quote_foot(button="Send enquiry"):
    return (f'<div class="qf-status" role="alert" hidden></div>'
            f'<button class="qf-btn" type="submit">{button}</button>'
            f'<p class="qf-call">Prefer to call? <a href="{PHONE_LINK}">{PHONE}</a></p>')


def quote_inline(p, qtype="rental", machine="", category="", toggle=True, sold=False):
    """Fields + submit for an inline <form class="qf" data-quote-form="inline" novalidate> written in a page partial."""
    return quote_fields(p, qtype, machine, category, toggle, sold) + '<div class="qf-foot">' + quote_foot() + "</div>"


def quote_modal():
    """The popup. Pages with a quote button get one copy just before </body> (not the Contact page)."""
    wa = f"https://wa.me/{WA_NUMBER}?text=" + "Hi%2C%20I%27d%20like%20a%20quote."
    return f'''<!-- Quote popup: copy of assets/partials/quote-modal.html (generated from _source/quote.py). Behaviour: assets/js/quote-modal.js -->
<dialog id="quote-modal" class="qm" aria-labelledby="qm-title" aria-describedby="qm-desc">
  <div class="qm-head">
    <h2 class="qm-title" id="qm-title">Get a quote</h2>
    <button type="button" class="qm-x" data-qm-close aria-label="Close">{X_SVG}</button>
  </div>
  <form class="qf qm-form" data-quote-form="popup" novalidate>
    <div class="qm-body">
      <p class="qm-desc" id="qm-desc">We reply within working hours, Mon–Sat 9:00–19:00.</p>
      <a class="qf-wa" data-qm-wa href="{wa}" target="_blank" rel="noopener" aria-label="WhatsApp us (opens in a new tab)">{WA_SVG}<span>WhatsApp us</span></a>
      <p class="qm-or"><span>or fill in the form</span></p>
      {quote_fields("qm-")}
    </div>
    <div class="qm-foot">{quote_foot()}</div>
  </form>
</dialog>'''
