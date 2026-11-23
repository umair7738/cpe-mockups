"""Cherry Pickers Equipment – HTML mockup builder (v3: /rental/{category}/ and /sales/ structure).

Pages mirror the final WordPress URLs as folders with index.html:
  /rental/                       rental landing (SEO content + image category tiles)
  /rental/{category}/            category listing with category-specific filters
  /sales/                        sales landing (SEO content + image category tiles)
  /sales/new/                    new equipment (empty-state + noindex while NEW is empty)
  /sales/used/                   filterable used stock listing
  /sales/sold/                   filterable sold records (212, from the live Sold page)
Partials in ./pages use flat names (e.g. href="contact.html"); rewrite_links() maps them to folder URLs.
"""
import json
import re
from urllib.parse import quote
import shutil
from collections import Counter, OrderedDict
from pathlib import Path
from PIL import Image as _PIL

from legacy import icon, WA_SVG, PHONE, PHONE_LINK, WA_LINK, ADDRESS, quick_form

SRC = Path(__file__).parent
OUT = Path(__file__).resolve().parent.parent
IMG = OUT / "assets" / "img"
SITE = "https://cherrypickersglobal.com/"

# ------------------------------------------------------------------ URL map (flat name -> folder URL)
LINKS = {
    "index.html": "",
    "about.html": "about/",
    "about-who-we-are.html": "about/who-we-are/",
    "about-what-we-do.html": "about/what-we-do/",
    "about-who-we-work-with.html": "about/who-we-work-with/",
    "about-our-story.html": "about/our-story/",
    "rental.html": "rental/",
    "rental-category.html": "rental/electric-scissor-lifts/",
    "rental-detail.html": "rental/electric-scissor-lifts/genie-gs-3246/",
    "sales.html": "sales/",
    "equipment-for-sale.html": "sales/",
    "sales-new.html": "sales/new/",
    "sales-used.html": "sales/used/",
    "sales-available.html": "sales/used/",  # alias for old partial links
    "sales-sold.html": "sales/sold/",
    "sale-detail.html": "sales/used/2010-jlg-600aj/",
    "services.html": "services/",
    "maintenance-repair.html": "services/maintenance-repair/",
    "services-amc.html": "services/amc/",
    "services-on-site-repairs.html": "services/on-site-repairs/",
    "services-workshop.html": "services/workshop-services/",
    "blog.html": "blog/",
    "blog-detail.html": "blog/boom-lift-vs-scissor-lift/",
    "contact.html": "contact/",
    "privacy-policy.html": "privacy-policy/",
    "terms-and-conditions.html": "terms-and-conditions/",
}

# ------------------------------------------------------------------ rental fleet (live Equipment Hire page, duplicates merged)
# key, model, brand, category, working h, platform h, outreach, capacity kg, weight kg, power, image, status
R = [
    ("gs1930", "Genie GS-1930", "Genie", "es", 7.79, 5.58, None, 227, 1505, "Electric", "r-gs1930", "ok"),
    ("gs1932", "Genie GS-1932", "Genie", "es", 7.81, 5.85, None, 227, 1329, "Electric", "r-gs1932", "ok"),
    ("gs2646", "Genie GS-2646", "Genie", "es", 9.9, 7.96, None, 454, 1956, "Electric", "r-gs2646", "busy"),
    ("gs3246", "Genie GS-3246", "Genie", "es", 11.75, 9.78, None, 318, 2812, "Electric", "r-gs3246", "ok"),
    ("3246es", "JLG 3246ES", "JLG", "es", 11.68, 9.68, None, 320, 2905, "Electric", "r-3246es", "ok"),
    ("d1412", "Dingli 1412HD", "Dingli", "es", 13.8, 11.8, None, 320, 3380, "Electric", "r-dingli1412", "ok"),
    ("m4069", "JLG M4069LE", "JLG", "es", 14.19, 12.19, None, 362, 4926, "Electric", "r-m4069le", "ok"),
    ("d1612", "Dingli 1612HD", "Dingli", "es", 15.7, 13.7, None, 250, 3360, "Electric", "r-dingli1612", "ok"),
    ("gs4390", "Genie GS-4390 RT", "Genie", "rt", 15.11, 13.11, None, 680, 5937, "Diesel", "r-gs4390rt", "ok"),
    ("gs5390", "Genie GS-5390 RT", "Genie", "rt", 18.15, 16.15, None, 680, 7515, "Diesel", "r-gs5390", "ok"),
    ("ab38e", "Snorkel AB38E", "Snorkel", "eb", 13.5, None, 6.1, 215, 3880, "Electric", "r-ab38e", "ok"),
    ("e450aj", "JLG E450AJ", "JLG", "eb", 15.7, None, 7.24, 227, 6532, "Electric", "r-e450aj", "ok"),
    ("600jp", "JLG 600JP", "JLG", "eb", 20.39, None, 13.54, 230, 7815, "Electric", "r-600jp", "ok"),
    ("450aj", "JLG 450AJ", "JLG", "ab", 15.72, None, 7.62, 250, 6418, "Diesel", "r-450aj", "ok"),
    ("z4525", "Genie Z-45/25", "Genie", "ab", 15.9, None, 7.65, 227, 7400, "Diesel", "r-z4525", "ok"),
    ("z4525ic", "Genie Z-45/25 IC", "Genie", "ab", 15.9, None, 7.65, 227, 7598, "Diesel", "r-z4525ic", "ok"),
    ("z4525j", "Genie Z-45/25J", "Genie", "ab", 15.94, None, 7.65, 227, 6515, "Diesel", "r-z4525j", "ok"),
    ("510aj", "JLG 510AJ", "JLG", "ab", 17.81, None, 9.48, 230, 7650, "Diesel", "r-510aj", "ok"),
    ("z6034", "Genie Z-60/34", "Genie", "ab", 20.39, None, 11.05, 227, 11200, "Diesel", "r-z6034", "ok"),
    ("600aj", "JLG 600AJ", "JLG", "ab", 20.47, None, 12.10, 227, 10455, "Diesel", "r-600aj", "busy"),
    ("z6240", "Genie Z-62/40", "Genie", "ab", 20.87, None, 12.42, 227, 10063, "Diesel", "r-z6240", "ok"),
    ("800aj", "JLG 800AJ", "JLG", "ab", 26.32, None, 15.8, 227, 15757, "Diesel", "r-800aj", "ok"),
    ("z135", "Genie Z-135/70", "Genie", "ab", 43.15, None, 21.25, 272, 30000, "Diesel", "r-z135", "ok"),
    ("s45", "Genie S-45", "Genie", "tb", 15.7, None, 11.02, 227, 6926, "Diesel", "r-s45", "ok"),
    ("460sj", "JLG 460SJ", "JLG", "tb", 16.0, None, 12.34, 272, 8000, "Diesel", "r-460sj", "ok"),
    ("s65", "Genie S-65", "Genie", "tb", 21.8, None, 17.12, 227, 10531, "Diesel", "r-s65", "ok"),
    ("660sj", "JLG 660SJ", "JLG", "tb", 22.12, None, 17.4, 340, 12528, "Diesel", "r-660sj", "ok"),
    ("s80x", "Genie S-80X", "Genie", "tb", 26.21, None, 21.8, 454, 16329, "Diesel", "r-s80x", "ok"),
    ("s85", "Genie S-85", "Genie", "tb", 27.9, None, 23.32, 227, 18126, "Diesel", "r-s85", "ok"),
    ("860sj", "JLG 860SJ", "JLG", "tb", 28.21, None, 22.86, 340, 17200, "Diesel", "r-860sj", "ok"),
]
RENTAL = {r[0]: r for r in R}
CONTAIN = {"r-gs5390", "r-z4525j", "r-z4525ic", "r-800aj", "r-gs1932", "r-510aj", "r-s80x", "r-z6034"}

# ------------------------------------------------------------------ rental categories
CATS = OrderedDict()
CATS["es"] = dict(
    slug="electric-scissor-lifts", name="Electric Scissor Lifts", one="Electric Scissor Lift", img="cat-electric-scissor",
    short="Quiet, zero-emission platforms for indoor fit-out, warehouses and malls.",
    h1="Electric Scissor Lift Rental in Dubai & UAE",
    intro="Electric scissor lifts are quiet, zero-emission work platforms that lift workers and tools straight up. We rent {n} electric scissor lift models from {lo} to {hi} working height for indoor fit-out, warehouses, malls and maintenance work, by the day, week or month, across all seven emirates.",
    hb=[(0, 10, "Up to 10 m"), (10, 13, "10 – 13 m"), (13, 99, "13 m and above")],
    second=("cap", "Platform capacity", [(0, 300, "Up to 300 kg"), (300, 400, "300 – 399 kg"), (400, 9999, "400 kg and above")]),
    uses=["Ceiling, lighting and MEP installation", "Warehouse racking and maintenance", "Mall, airport and hotel interior work",
          "Painting, signage and fit-out", "Facility maintenance on smooth, level floors"],
    choose=[("Working height", "Working height is platform height plus about 2 m (a person's reach). Pick a machine a little above your highest work point."),
            ("Width and doors", "Check door and corridor widths before you book – small slab scissors pass through standard doors."),
            ("Floor", "Electric scissor lifts need smooth, firm, level floors. For outdoor or rough ground, choose a rough terrain scissor lift."),
            ("Weight on the platform", "Add up people, tools and materials. Our electric scissors carry 227 kg to 454 kg.")],
    faq=[("What is the difference between working height and platform height?", "Platform height is how high the platform floor goes. Working height adds about 2 m for the person's reach. A Genie GS-3246 has a 9.78 m platform height and an 11.75 m working height."),
         ("Can electric scissor lifts be used outdoors?", "Some models can work outdoors on firm, level ground in low wind. For uneven ground or strong wind, choose a rough terrain scissor lift."),
         ("Can I rent an electric scissor lift for one day?", "Yes. We rent by the day, week or month, and long-term."),
         ("Do you supply an operator?", "Yes, on request. Tell us when you book.")])
CATS["rt"] = dict(
    slug="rough-terrain-scissor-lifts", name="Rough Terrain Scissor Lifts", one="Rough Terrain Scissor Lift", img="cat-rt-scissor",
    short="Diesel 4x4 platforms with big decks for outdoor sites and uneven ground.",
    h1="Rough Terrain Scissor Lift Rental in Dubai & UAE",
    intro="Rough terrain scissor lifts are diesel work platforms with four-wheel drive and large decks, built for outdoor sites and uneven ground. We rent {n} rough terrain models from {lo} to {hi} working height, each carrying up to 680 kg, across all seven emirates.",
    hb=[(0, 16, "Up to 16 m"), (16, 99, "16 m and above")],
    second=("cap", "Platform capacity", [(600, 9999, "600 kg and above")]),
    uses=["Construction sites and building shells", "Cladding, facade and glazing work", "Steel and structural installation",
          "Outdoor events and exhibitions", "Infrastructure and industrial yards"],
    choose=[("Ground conditions", "Rough terrain models handle compacted soil, gravel and slopes – check the site gradient before booking."),
            ("Deck size and load", "Large decks carry crews, panels and tools together – up to 680 kg on our machines."),
            ("Working height", "Our rough terrain scissors reach 15.1 m to 18.2 m."),
            ("Access and transport", "These machines are large and heavy (5.9 – 7.5 tonnes) – confirm site access for delivery.")],
    faq=[("Can a rough terrain scissor lift be used indoors?", "They run on diesel, so they are not suited to enclosed spaces without proper ventilation. Indoors, use an electric scissor lift."),
         ("How much weight can a rough terrain scissor lift carry?", "Our Genie GS-4390 RT and GS-5390 RT carry up to 680 kg – people, tools and materials together."),
         ("What is the difference between a rough terrain and an electric scissor lift?", "Rough terrain models are diesel, 4x4 and built for outdoor ground. Electric models are quiet and compact, for smooth indoor floors.")])
CATS["eb"] = dict(
    slug="electric-boom-lifts", name="Electric Boom Lifts", one="Electric Boom Lift", img="cat-electric-boom",
    short="Battery booms that reach up and over – indoors or in noise-sensitive areas.",
    h1="Electric Boom Lift Rental in Dubai & UAE",
    intro="Electric boom lifts are battery-powered booms that reach up and out over obstacles with no exhaust and little noise. We rent {n} electric boom lift models from {lo} to {hi} working height for indoor atriums, malls, airports and night work, across all seven emirates.",
    hb=[(0, 15, "Up to 15 m"), (15, 18, "15 – 18 m"), (18, 99, "18 m and above")],
    second=("out", "Horizontal outreach", [(0, 8, "Up to 8 m"), (8, 99, "8 m and above")]),
    uses=["Atriums, malls and airport terminals", "Warehouse and factory maintenance", "Work over machinery or seating",
          "Night work in noise-sensitive areas", "Lighting, ductwork and sprinkler installation"],
    choose=[("Outreach", "Check how far you need to reach sideways, not only up – our electric booms reach 6.1 m to 13.5 m out."),
            ("Floor loading", "Booms are heavier than scissors (3.9 – 7.8 tonnes). Confirm the floor can take the machine."),
            ("Shift length", "[Add: typical battery runtime and charging needs for your machines.]"),
            ("Indoor or outdoor", "Electric booms are ideal indoors; some also work outdoors on firm ground.")],
    faq=[("Can electric boom lifts be used outdoors?", "Yes, on firm and level ground within the machine's wind rating. For rough ground, choose a diesel articulated or telescopic boom."),
         ("How long does the battery last?", "[Your answer – typical hours per charge for your machines.]"),
         ("What is the highest electric boom you rent?", "The JLG 600JP, with a 20.39 m working height and 13.54 m outreach.")])
CATS["ab"] = dict(
    slug="articulated-boom-lifts", name="Articulated Boom Lifts", one="Articulated Boom Lift", img="cat-articulated",
    short="Jointed booms that bend up and over obstacles to reach tight spots.",
    h1="Articulated Boom Lift Rental in Dubai & UAE",
    intro="Articulated boom lifts (knuckle booms) have jointed arms that bend up and over obstacles to reach tight spots. We rent {n} articulated boom models from {lo} to {hi} working height – including the Genie Z-135/70 – across all seven emirates.",
    hb=[(0, 16, "Up to 16 m"), (16, 21, "16 – 21 m"), (21, 99, "21 m and above")],
    second=("out", "Horizontal outreach", [(0, 10, "Up to 10 m"), (10, 15, "10 – 15 m"), (15, 99, "15 m and above")]),
    uses=["Piping and MEP work over obstacles", "Steel structures and roof work", "Tanks, plants and industrial facilities",
          "Building maintenance and repairs", "Work behind or above other equipment"],
    choose=[("Up-and-over clearance", "Articulated booms bend over obstacles. If nothing is in the way, a telescopic boom may reach further."),
            ("Outreach", "Our articulated booms reach 7.6 m to 21.3 m sideways."),
            ("Ground", "Diesel 4x4 models work on rough sites; check slope and ground bearing."),
            ("Height", "From 15.7 m for everyday work up to 43.15 m with the Genie Z-135/70.")],
    faq=[("What is the difference between an articulated and a telescopic boom lift?", "An articulated boom has joints that bend up and over obstacles. A telescopic boom extends straight out for maximum reach. Choose articulated when something is in the way."),
         ("What is the tallest articulated boom you rent?", "The Genie Z-135/70, with a 43.15 m working height and 21.25 m outreach."),
         ("Do you supply an operator?", "Yes, on request. Tell us when you book.")])
CATS["tb"] = dict(
    slug="telescopic-boom-lifts", name="Telescopic Boom Lifts", one="Telescopic Boom Lift", img="cat-telescopic",
    short="Straight booms for maximum height and reach on facades and steel work.",
    h1="Telescopic Boom Lift Rental in Dubai & UAE",
    intro="Telescopic boom lifts (straight booms) extend straight out for the most height and horizontal reach from one position. We rent {n} telescopic boom models from {lo} to {hi} working height for facades, steel erection and large structures across all seven emirates.",
    hb=[(0, 20, "Up to 20 m"), (20, 25, "20 – 25 m"), (25, 99, "25 m and above")],
    second=("out", "Horizontal outreach", [(0, 15, "Up to 15 m"), (15, 20, "15 – 20 m"), (20, 99, "20 m and above")]),
    uses=["Facades, glazing and cladding", "Steel erection and large-span structures", "Bridges and infrastructure",
          "Signage and high-level installation", "Tree work and outdoor maintenance"],
    choose=[("Reach vs height", "Telescopic booms give the longest outreach – up to 23.3 m on the Genie S-85."),
            ("Platform load", "Need more on the platform? The Genie S-80X carries 454 kg; JLG 660SJ and 860SJ carry 340 kg."),
            ("Clear path", "A straight boom needs a clear line to the work point. If obstacles are in the way, use an articulated boom."),
            ("Ground and access", "These are heavy machines (6.9 – 18.1 tonnes) – check ground bearing and site access.")],
    faq=[("Which telescopic boom has the longest reach?", "The Genie S-85, with 23.32 m horizontal outreach and 27.9 m working height."),
         ("Which telescopic boom carries the most weight?", "The Genie S-80X, with a 454 kg platform capacity."),
         ("Telescopic or articulated – which do I need?", "Telescopic for the longest straight reach; articulated when you need to go up and over obstacles.")])

for k, c in CATS.items():
    ms = [r for r in R if r[3] == k]
    c["key"] = k
    c["models"] = ms
    c["n"] = len(ms)
    c["lo"] = f"{min(r[4] for r in ms):g} m"
    c["hi"] = f"{max(r[4] for r in ms):g} m"
    c["range"] = f"{min(r[4] for r in ms):.1f} – {max(r[4] for r in ms):.1f} m"
    c["file"] = f"rental-{c['slug']}.html"
    LINKS[c["file"]] = f"rental/{c['slug']}/"
N_RENTAL = len(R)

# ------------------------------------------------------------------ sales stock (page 1 of live "Available for Sale", duplicate serial merged)
# id, year, model, brand, type, origin, working height, image or None, note
SALE = [
    ("a1", 2011, "JLG 860SJ", "JLG", "T", "Australia", 28.2, "s-860sj", ""),
    ("a2", 2008, "JLG 660SJ", "JLG", "T", "Spain", 22.1, "s-660sj-2008", ""),
    ("a3", 2007, "JLG 660SJ", "JLG", "T", "Spain", 22.1, None, "Listing photo shows a different machine"),
    ("a4", 2018, "JLG E450AJ", "JLG", "A", "Singapore", 15.7, "s-e450aj-2", "2nd unit"),
    ("a5", 2011, "JLG M450AJ", "JLG", "A", "Poland", 15.7, "s-m450aj", ""),
    ("a6", 2018, "JLG E450AJ", "JLG", "A", "Singapore", 15.7, "s-e450aj", "1st unit"),
    ("a7", 2006, "JLG 1350SJP", "JLG", "T", "Denmark", 43.1, None, "Listing photo needs checking"),
    ("a8", 2009, "JLG 1350SJP", "JLG", "T", "Hong Kong", 43.1, "s-1350sjp", "Listed twice (same serial)"),
    ("a10", 2004, "JLG 860SJ", "JLG", "T", "Netherlands", 28.2, "s-860sj-2004", ""),
    ("a11", 2007, "JLG 860SJ", "JLG", "T", "Netherlands", 28.2, None, "Listing photo shows a Genie boom"),
    ("a12", 2006, "Genie S-65", "Genie", "T", "Poland", 21.8, None, "Listing photo shows a JLG data plate"),
    ("a13", 2010, "JLG 600AJ", "JLG", "A", "Australia", 20.5, "s-600aj-1", ""),
    ("a14", 2008, "JLG 600AJ", "JLG", "A", "Australia", 20.5, None, "Listing photo shows a telescopic boom"),
    ("a15", 2008, "JLG 1200SJP", "JLG", "T", "Denmark", 38.6, "s-1200sjp", ""),
    ("a16", 2006, "JLG 1200SJP", "JLG", "T", "Denmark", 38.6, None, "Listing photo shows only a platform"),
    ("a17", 2007, "JLG 860SJ", "JLG", "T", "Denmark", 28.2, None, "No photo on listing"),
]
# New equipment for sale (same tuple format as SALE). Empty = /sales/new/ shows an enquiry panel and is noindexed.
NEW = []
SALEMAP = {s[0]: s for s in SALE + NEW}
TYPES = {"T": ("telescopic", "Telescopic Boom Lift"), "A": ("articulated", "Articulated Boom Lift"),
         "S": ("scissor", "Scissor Lift"), "R": ("scissor", "Scissor Lift"), "E": ("electric-boom", "Electric Boom Lift")}

# ------------------------------------------------------------------ sold records
SOLD = []
for line in (SRC / "data" / "sold.txt").read_text(encoding="utf-8").splitlines():
    if not line.strip() or line.startswith("#"):
        continue
    m, y, o, t, to, d = line.split("|")
    SOLD.append(dict(id=str(len(SOLD) + 1), model=m, year=int(y), origin=o, t=t, to=to or "", date=d or ""))
N_SOLD = len(SOLD)
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

# Sold cards/pages show a photo of the same MODEL from our rental fleet or sales stock (labelled "Model photo"),
# because the sold records have no photos of the actual unit. Models not listed here get a grey placeholder.
SOLD_IMG = {
    "JLG 660SJ": "r-660sj", "JLG 860SJ": "r-860sj", "Genie S-65": "r-s65", "JLG 600AJ": "r-600aj",
    "JLG 1200SJP": "s-1200sjp", "JLG 1350SJP": "s-1350sjp", "JLG 800AJ": "r-800aj", "JLG E450AJ": "r-e450aj",
    "Genie S-85": "r-s85", "JLG 510AJ": "r-510aj", "JLG M450AJ": "s-m450aj", "Genie GS-5390 RT": "r-gs5390",
    "Genie Z-135/70": "r-z135", "JLG 460SJ": "r-460sj", "JLG 450AJ": "r-450aj",
}
SOLD_IMG = {k: v for k, v in SOLD_IMG.items() if (IMG / f"{v}-sm.webp").exists()}
# Model specs we already hold: rental fleet (full specs) and sales stock (working height only)
MODEL_RENT = {r[1]: r for r in R}
MODEL_WH = {s[2]: s[6] for s in SALE}
MODEL_WH.update({r[1]: r[4] for r in R})


def fmt_date(d):
    if not d:
        return "—"
    y, mo = d.split("-")
    return y if mo == "00" else f"{MONTHS[int(mo) - 1]} {y}"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def band(v, bands):
    for lo, hi, label in bands:
        if lo <= v < hi:
            return slug(label), label
    return None, None


# ------------------------------------------------------------------ per-machine detail pages (flat token -> folder URL)
# rent-<key>.html -> rental/<category-slug>/<model-slug>/   e.g. rental/telescopic-boom-lifts/genie-s-65/
# sale-<id>.html  -> sales/used/<year>-<model-slug>/        e.g. sales/used/2011-jlg-860sj/
# The same year + model listed twice gets "-2" on the later one (WordPress does the same for duplicate slugs).
for _r in R:
    LINKS[f"rent-{_r[0]}.html"] = f"rental/{CATS[_r[3]]['slug']}/{slug(_r[1])}/"
_seen = Counter()
for _s in SALE:
    _base = f"{_s[1]}-{slug(_s[2])}"
    _seen[_base] += 1
    LINKS[f"sale-{_s[0]}.html"] = f"sales/used/{_base}{'' if _seen[_base] == 1 else '-' + str(_seen[_base])}/"
# sold-<n>.html -> sales/sold/<year>-<model-slug>/   e.g. sales/sold/2015-jlg-860sj/  (same "-2" rule for repeats)
_seen = Counter()
for _s in SOLD:
    _base = f"{_s['year']}-{slug(_s['model'])}"
    _seen[_base] += 1
    LINKS[f"sold-{_s['id']}.html"] = f"sales/sold/{_base}{'' if _seen[_base] == 1 else '-' + str(_seen[_base])}/"
# The mockup builds one sample sold detail page (like the one rental and one used-sale sample); WordPress renders the rest.
SOLD_SAMPLE = next(s for s in SOLD if s["model"] == "JLG 860SJ" and s["year"] == 2015 and s["to"] and s["date"])
SOLD_SAMPLE_PATH = LINKS[f"sold-{SOLD_SAMPLE['id']}.html"] + "index.html"

# Sales machine type letter -> rental category slug (so ?category= works the same on rental and sales listings)
TYPE_CAT = {"T": "telescopic-boom-lifts", "A": "articulated-boom-lifts", "E": "electric-boom-lifts",
            "S": "electric-scissor-lifts", "R": "rough-terrain-scissor-lifts"}
SLUG_CAT = {c["slug"]: c for c in CATS.values()}


# ------------------------------------------------------------------ media
def media(name, alt, cls="ratio-4-3", eager=False, label=""):
    f = IMG / f"{name}.webp"
    w, h = _PIL.open(f).size
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    lab = f' data-label="{label}"' if label else ""
    return (f'<div class="media {cls}"{lab}><img src="assets/img/{name}.webp" alt="{alt}" '
            f'width="{w}" height="{h}" {load} decoding="async"></div>')


def hero_img(name, alt):
    """Full-width background photo for a .r-hero section (LCP: eager, high priority). Falls back to the -sm file."""
    if not (IMG / f"{name}.webp").exists():
        name += "-sm"
    w, h = _PIL.open(IMG / f"{name}.webp").size
    return f'<img src="assets/img/{name}.webp" alt="{alt}" width="{w}" height="{h}" fetchpriority="high" decoding="async">'


def img_tag(name, alt, eager=False, style=""):
    """Plain <img> with real width/height (no layout shift). Lazy unless eager (above the fold)."""
    w, h = _PIL.open(IMG / f"{name}.webp").size
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    st = f' style="{style}"' if style else ""
    return f'<img src="assets/img/{name}.webp" alt="{alt}" width="{w}" height="{h}" {load} decoding="async"{st}>'


def wa_url(msg):
    """wa.me link with a pre-filled message (HTML-attribute safe)."""
    return f"{WA_LINK}?text={quote(msg, safe='')}"


STATUS = {"ok": '<span class="badge badge--ok">Available</span>',
          "busy": '<span class="badge badge--busy">On hire – ask for date</span>'}


# ------------------------------------------------------------------ cards
def rental_card(key, facets=""):
    k, m, brand, cat, wh, ph, out, cap, wt, pw, img, st = RENTAL[key]
    c = CATS[cat]
    fit = " contain" if img in CONTAIN else ""
    mid = (f"<div><strong>{ph:g} m</strong>Platform ht.</div>" if ph else f"<div><strong>{out:g} m</strong>Outreach</div>")
    return f'''<article class="machine-card" data-item data-facets="{facets}" data-s-height="{wh}" data-s-cap="{cap}">
  <div class="card-top-badges">{STATUS[st]}</div>
  {media(img + "-sm", f"{m} {c['one'].lower()} for rent in Dubai", "ratio-4-3" + fit)}
  <div class="machine-card-body">
    <div>
      <h3><a href="rent-{k}.html">{m}</a></h3>
      <div class="machine-type">{c['one']} · {pw}</div>
    </div>
    <div class="spec-mini">
      <div><strong>{wh:g} m</strong>Working ht.</div>
      {mid}
      <div><strong>{cap} kg</strong>Capacity</div>
    </div>
    <div class="machine-actions">
      <a class="btn btn--ghost btn--sm" href="rent-{k}.html" style="justify-content:center">Details</a>
      <a class="btn btn--red btn--sm" href="contact.html#enquiry" style="justify-content:center">Get a Quote</a>
    </div>
  </div>
</article>'''


def sale_card(sid, facets=""):
    i, y, m, brand, t, origin, wh, img, note = SALEMAP[sid]
    tname = TYPES[t][1]
    if img:
        pic = media(img + "-sm", f"Used {y} {m} {tname.lower()} for sale", "ratio-4-3")
    else:
        pic = '<div class="ph ratio-4-3 ph--req" data-label="Photos on request"></div>'
    href = f"sale-{i}.html" if f"sale-{i}.html" in LINKS else "sales-new.html"
    return f'''<article class="machine-card" data-item data-facets="{facets}" data-s-year="{y}" data-s-height="{wh}">
  {pic}
  <div class="machine-card-body">
    <div>
      <h3><a href="{href}">{y} {m}</a></h3>
      <div class="machine-type">{tname} · Origin: {origin}</div>
    </div>
    <div class="spec-mini">
      <div><strong>{y}</strong>Year</div>
      <div><strong>{wh:g} m</strong>Working ht.</div>
      <div><strong>{brand}</strong>Brand</div>
    </div>
    <div class="price">Contact for price <small>UAE &amp; export enquiries</small></div>
    <div class="machine-actions">
      <a class="btn btn--ghost btn--sm" href="{href}" style="justify-content:center">Details</a>
      <a class="btn btn--red btn--sm" href="contact.html#enquiry" style="justify-content:center">Enquire</a>
    </div>
  </div>
</article>'''


def sold_pic(s, cls="ratio-4-3", eager=False, label="Model photo"):
    """Model photo for a sold record (greyed by .is-sold on cards), or a placeholder when we have no photo of the model."""
    img = SOLD_IMG.get(s["model"])
    tname = TYPES[s["t"]][1].lower()
    if not img:
        ph = " ph--scissor" if s["t"] in ("S", "R") else ""
        return f'<div class="ph {cls} ph--req{ph}" data-label="No photo of this model yet"></div>'
    name = img if eager and (IMG / f"{img}.webp").exists() else img + "-sm"
    fit = " contain" if img in CONTAIN else ""
    return media(name, f"{s['model']} {tname} – model photo, sold machine", cls + fit, eager, label)


def sold_card(s, facets=""):
    """Sold record card – same structure as the used-sale card, with a Sold badge and greyed photo."""
    tname = TYPES[s["t"]][1]
    href = f"sold-{s['id']}.html"
    dkey = s["date"].replace("-", "") if s["date"] else "0"
    return f'''<article class="machine-card is-sold" data-item data-facets="{facets}" data-s-date="{dkey}" data-s-year="{s["year"]}">
  <div class="card-top-badges"><span class="badge badge--sold">Sold</span></div>
  {sold_pic(s)}
  <div class="machine-card-body">
    <div>
      <h3><a href="{href}">{s["year"]} {s["model"]}</a></h3>
      <div class="machine-type">{tname} · Origin: {s["origin"]}</div>
    </div>
    <div class="spec-mini">
      <div><strong>{s["year"]}</strong>Year</div>
      <div><strong>{s["to"] or "—"}</strong>Sold to</div>
      <div><strong>{fmt_date(s["date"])}</strong>Sold</div>
    </div>
    <div class="machine-actions">
      <a class="btn btn--ghost btn--sm" href="{href}" style="justify-content:center">Details</a>
      <a class="btn btn--red btn--sm" href="contact.html#enquiry" style="justify-content:center">Find Me One</a>
    </div>
  </div>
</article>'''


# ------------------------------------------------------------------ filter sidebar (counts computed from data)
def filter_group(title, key, options):
    """options: list of (value, label, count)"""
    rows = "".join(
        f'<label data-label="{lab}"><input type="checkbox" name="{key}" value="{v}"> {lab} <span class="count">{n}</span></label>'
        for v, lab, n in options)
    return f'<div class="filter-group"><h3>{title}</h3>{rows}</div>'


def sidebar(groups, total, noun):
    return f'''<aside class="filters" aria-label="Filter {noun}">
      <div class="filters-head"><h2>Filter</h2><div class="filters-head-actions"><a href="#" data-clear>Clear all</a><button type="button" class="filters-x" data-filter-dismiss aria-label="Close filters">&times;</button></div></div>
      {"".join(groups)}
      <div class="filter-close"><button class="btn btn--red btn--block" data-filter-close>Show {total} {noun}</button></div>
    </aside>'''


def listing_bar(total, noun, sorts):
    opts = "".join(f'<option value="{v}">{l}</option>' for v, l in sorts)
    return f'''<div class="listing-bar">
        <span class="result-count">Showing <strong><span data-result-count>{total}</span> {noun}</strong></span>
        <div class="listing-bar-actions">
          <button class="btn btn--ghost btn--sm filter-open" data-filter-open>{icon("filter")} Filter</button>
          <label class="sort-group"><span class="sort-label">Sort by:</span><select class="select" data-sort>{opts}</select></label>
        </div>
      </div>
      <div class="active-chips" data-active-chips></div>'''


EMPTY = '<div class="empty-state" data-empty hidden><strong>No machines match these filters.</strong><br><a href="#" data-clear>Clear filters</a> or <a href="contact.html#enquiry">ask us to source one</a>.</div>'


def faq_html(items):
    out = []
    for n, (q, a) in enumerate(items):
        op = " open" if n == 0 else ""
        out.append(f'<details{op}><summary><h3>{q}</h3></summary><div><p>{a}</p></div></details>')
    return '<div class="faq">' + "".join(out) + "</div>"


# ================================================================== RENTAL LANDING
def page_rental_landing():
    tiles = []
    for c in CATS.values():
        tiles.append(f'''<a class="tile" href="{c['file']}">
        {media(c['img'] + '-sm', c['one'] + ' rental in Dubai', 'tile-img')}
        <div class="tile-body">
          <span class="tile-meta">{c['n']} models · {c['range']}</span>
          <h3>{c['name']}</h3>
          <p>{c['short']}</p>
          <span class="tile-link">View {c['name'].lower()} →</span>
        </div>
      </a>''')
    # Spider lifts: not in the current fleet, so the tile goes to an enquiry instead of a category page
    tiles.append(f'''<a class="tile" href="contact.html#enquiry">
        {media('cat-spider-sm', 'Tracked spider lift for rent in Dubai', 'tile-img')}
        <div class="tile-body">
          <span class="tile-meta">On request</span>
          <h3>Spider Lifts</h3>
          <p>Compact tracked booms that fit through doorways and set up on slopes, stairs and soft ground.</p>
          <span class="tile-link">Ask about spider lifts →</span>
        </div>
      </a>''')
    # height finder table
    bands = [(0, 10, "Up to 10 m"), (10, 16, "10 – 16 m"), (16, 22, "16 – 22 m"), (22, 99, "22 m and above")]
    rows = []
    for lo, hi, lab in bands:
        cells = []
        for c in CATS.values():
            ms = [r for r in c["models"] if lo <= r[4] < hi]
            if ms:
                cells.append(f'<a href="{c["file"]}"><strong>{c["name"]}</strong></a><br><span class="small muted">{", ".join(r[1] for r in ms)}</span>')
        rows.append(f'<tr><td><strong>{lab}</strong></td><td>{"<hr class=\"cell-hr\">".join(cells)}</td></tr>')
    # full fleet listing: the home page machine finder lands here with ?category=<slug>&height=<min-max>
    fc, fh, fb = Counter(), Counter(), Counter()
    cards = []
    for r in sorted(R, key=lambda r: r[4]):
        cv = CATS[r[3]]["slug"]; hv, _ = band(r[4], bands); bv = slug(r[2])
        fc[cv] += 1; fh[hv] += 1; fb[bv] += 1
        cards.append(rental_card(r[0], f"category={cv} height={hv} brand={bv}"))
    fleet_groups = [
        filter_group("Machine type", "category", [(c["slug"], c["name"], fc[c["slug"]]) for c in CATS.values()]),
        filter_group("Working height", "height", [(slug(l), l, fh[slug(l)]) for _, _, l in bands if fh[slug(l)]]),
        filter_group("Brand", "brand", [(b, "JLG" if b == "jlg" else b.title(), n) for b, n in sorted(fb.items())]),
    ]
    faq = [
        ("What access equipment can I rent from Cherry Pickers Equipment?", f"We rent {N_RENTAL} models across five types: electric scissor lifts, rough terrain scissor lifts, electric boom lifts, articulated boom lifts and telescopic boom lifts, from 7.8 m to 43 m working height. Spider lifts are available on request."),
        ("What is a spider lift and when do I need one?", "A spider lift is a compact boom on rubber tracks with outriggers. It fits through standard doorways, is light on delicate floors and levels itself on slopes, stairs or soft ground. Ask us when access is tight or the floor cannot take a standard boom."),
        ("What is the minimum rental period?", "You can rent for a single day. We also offer weekly, monthly and long-term hire."),
        ("Do you deliver outside Dubai?", "Yes. We deliver and collect across all seven emirates: Dubai, Abu Dhabi, Sharjah, Ajman, Ras Al Khaimah, Fujairah and Umm Al Quwain."),
        ("Do you supply operators?", "Yes, on request. Tell us when you book and we will include an operator with the machine."),
        ("How do I choose between a scissor lift and a boom lift?", "Choose a scissor lift to go straight up with a large platform. Choose a boom lift when you need to reach up and out, or over obstacles."),
    ]
    return f'''<!-- 1. HERO: full-width photo (LCP, eager) + answer-first text -->
<section class="r-hero">
  {hero_img("cat-articulated", "Articulated boom lift for rent on a UAE construction site")}
  <div class="wrap r-hero-inner">
    <span class="eyebrow">Access equipment rental · UAE</span>
    <h1>Scissor Lift &amp; Boom Lift Rental in Dubai and the UAE</h1>
    <p class="hero-lead">Rent from {N_RENTAL} models of scissor lifts and boom lifts – 7.8 m to 43 m working height – for daily, weekly, monthly or long-term hire. Delivered to your site across all seven emirates, with operators on request.</p>
    <div class="hero-actions">
      <a class="btn btn--red" href="#categories">Find Your Machine</a>
      <a class="btn btn--wa" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp for a Quote</a>
    </div>
  </div>
</section>

<!-- 2. CATEGORY TILES: image cards, each links to /rental/{{category}}/ -->
<section class="section" id="categories">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Choose a machine type</span>
      <h2>Our Rental Equipment Categories</h2>
      <p>Pick a category to see every machine we have, with working height, outreach and capacity – and filter to the one that fits your job.</p>
    </div>
    <div class="tiles">
      {"".join(tiles)}
    </div>
  </div>
</section>

<!-- 2b. ALL RENTAL MACHINES: filterable list of the whole fleet (target of the home page machine finder) -->
<section class="section section--alt" id="all-machines" style="padding-top:40px">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Full fleet</span>
      <h2>All Rental Machines</h2>
      <p>Filter all {N_RENTAL} models by machine type, working height and brand.</p>
    </div>
    <div class="listing">
      {sidebar(fleet_groups, N_RENTAL, "machines")}
      <div>
        {listing_bar(N_RENTAL, "machines", [("height-asc", "Working height (low to high)"), ("height-desc", "Working height (high to low)"), ("cap-desc", "Capacity (highest first)")])}
        <div class="grid grid-3" data-listing data-page-size="9" data-noun="machines">
          {"".join(cards)}
        </div>
        {EMPTY}
        <div class="center mt-24"><button class="btn btn--ghost" data-more>Show more machines</button></div>
      </div>
    </div>
  </div>
</section>

<!-- 3. HEIGHT FINDER: answer-style table (good for Google and AI answers) -->
<section class="section section--alt">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Height finder</span>
      <h2>Which Machine Do I Need for My Working Height?</h2>
      <p>Working height = platform height + about 2 m. Find your height, then open the category.</p>
    </div>
    <div class="table-wrap">
      <table class="finder">
        <thead><tr><th style="width:180px">Working height</th><th>Machines in our fleet</th></tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </div>
  </div>
</section>

<!-- 4. SCISSOR vs BOOM vs SPIDER -->
<section class="section">
  <div class="wrap">
    <div class="section-head section-head--center">
      <span class="eyebrow">Quick guide</span>
      <h2>Scissor Lift, Boom Lift or Spider Lift?</h2>
    </div>
    <div class="grid grid-3 guide-3">
      <div class="split-panel">
        <h3 style="font-size:1.5rem">Choose a scissor lift when…</h3>
        <ul class="tick-list">
          <li>You need to go <strong>straight up</strong></li>
          <li>Several people, tools or materials go on the platform</li>
          <li>The work area is directly above the machine</li>
          <li>Indoors on smooth floors (electric) or outdoors on rough ground (rough terrain)</li>
        </ul>
        <a class="link-arrow" href="{CATS['es']['file']}">Electric scissor lifts →</a> &nbsp; <a class="link-arrow" href="{CATS['rt']['file']}">Rough terrain →</a>
      </div>
      <div class="split-panel split-panel--navy">
        <h3 style="font-size:1.5rem">Choose a boom lift when…</h3>
        <ul class="tick-list">
          <li>You need to reach <strong>up and out</strong>, away from the base</li>
          <li>Obstacles are in the way (articulated)</li>
          <li>You need the longest straight reach (telescopic)</li>
          <li>Quiet, zero-emission work indoors (electric boom)</li>
        </ul>
        <a class="link-arrow" style="color:#ff5a45" href="{CATS['ab']['file']}">Articulated →</a> &nbsp; <a class="link-arrow" style="color:#ff5a45" href="{CATS['tb']['file']}">Telescopic →</a> &nbsp; <a class="link-arrow" style="color:#ff5a45" href="{CATS['eb']['file']}">Electric boom →</a>
      </div>
      <div class="split-panel">
        <h3 style="font-size:1.5rem">Choose a spider lift when…</h3>
        <ul class="tick-list">
          <li>Access is <strong>tight</strong> – narrow doors, gates or corridors</li>
          <li>Floors are delicate or the ground is soft (light weight, non-marking tracks)</li>
          <li>You set up on slopes, steps or uneven ground (outriggers level the machine)</li>
          <li>Atriums, lobbies, glazing and tree work, indoors or outdoors</li>
        </ul>
        <a class="link-arrow" href="contact.html#enquiry">Ask about spider lifts →</a>
      </div>
    </div>
  </div>
</section>

<!-- 5. RENTAL OPTIONS + PROCESS -->
<section class="section section--alt">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">How rental works</span><h2>Flexible Hire, Delivered to Your Site</h2></div>
    <div class="grid grid-4">
      <div class="service-block"><div class="icon">{icon("calendar")}</div><h3>Daily to long-term</h3><p>Rent for a day, a week, a month or longer.</p></div>
      <div class="service-block"><div class="icon">{icon("truck")}</div><h3>All 7 emirates</h3><p>Delivery and collection anywhere in the UAE, as soon as possible.</p></div>
      <div class="service-block"><div class="icon">{icon("shield")}</div><h3>Inspected machines</h3><p>Every machine is checked before it leaves our yard.</p></div>
      <div class="service-block"><div class="icon">{icon("user")}</div><h3>Operators on request</h3><p>Need someone to run the machine? Ask when you book.</p></div>
    </div>
    <div class="grid grid-4 steps mt-40">
      <div class="step"><h3>Tell us what you need</h3><p>Working height, type of job, site location and dates.</p></div>
      <div class="step"><h3>Get the right machine</h3><p>We suggest the best machine and send your quote.</p></div>
      <div class="step"><h3>Delivery to your site</h3><p>We deliver the inspected machine anywhere in the UAE.</p></div>
      <div class="step"><h3>Work with support</h3><p>Our team supports you for the whole hire period.</p></div>
    </div>
  </div>
</section>

<!-- 6. INDUSTRIES -->
<section class="section section--tight">
  <div class="wrap">
    <h2 style="font-size:1.6rem">Who Rents From Us</h2>
    <div class="grid grid-3 mt-24">
      <div class="industry">{icon("hardhat")} Construction</div>
      <div class="industry">{icon("building")} Facility management</div>
      <div class="industry">{icon("plane")} Malls and airports</div>
      <div class="industry">{icon("warehouse")} Warehousing</div>
      <div class="industry">{icon("drop")} Industrial, oil and gas</div>
      <div class="industry">{icon("calendar")} Events and exhibitions</div>
    </div>
  </div>
</section>

<!-- 7. FAQ -->
<section class="section section--alt">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">FAQ</span><h2>Equipment Rental Questions</h2></div>
    {faq_html(faq)}
  </div>
</section>

<!-- 8. GUIDES -->
<section class="section section--tight">
  <div class="wrap">
    <h2 style="font-size:1.6rem">Rental Guides</h2>
    <div class="cat-chips">
      <a class="chip" href="blog-detail.html">Boom Lift vs Scissor Lift: How to Choose</a>
      <a class="chip" href="blog-detail.html">Articulated vs Telescopic Boom Lift</a>
      <a class="chip" href="blog-detail.html">Working Height vs Platform Height</a>
    </div>
  </div>
</section>

{{{{cta:Need a Machine for Your Project?|Tell us the working height, the job and the site location. We'll suggest the right machine and send a quote.}}}}
'''


# ================================================================== RENTAL CATEGORY LISTING
def page_rental_category(c):
    ms = c["models"]
    hb = c["hb"]
    skey, stitle, sbands = c["second"]
    items = []
    fh, fs, fb, fa = Counter(), Counter(), Counter(), Counter()
    for r in sorted(ms, key=lambda r: r[4]):
        hv, _ = band(r[4], hb)
        sv, _ = band(r[7] if skey == "cap" else r[6], sbands)
        bv = slug(r[2])
        av = "available" if r[11] == "ok" else "on-hire"
        fh[hv] += 1; fs[sv] += 1; fb[bv] += 1; fa[av] += 1
        items.append(rental_card(r[0], f"height={hv} {skey}={sv} brand={bv} avail={av}"))
    groups = [
        filter_group("Working height", "height", [(slug(l), l, fh[slug(l)]) for _, _, l in hb if fh[slug(l)]]),
        filter_group(stitle, skey, [(slug(l), l, fs[slug(l)]) for _, _, l in sbands if fs[slug(l)]]),
        filter_group("Brand", "brand", [(b, b.title() if b != "jlg" else "JLG", n) for b, n in sorted(fb.items())]),
        filter_group("Availability", "avail", [(v, l, fa[v]) for v, l in (("available", "Available now"), ("on-hire", "On hire")) if fa[v]]),
    ]
    switch = "".join(
        f'<a class="chip{" chip--active" if o["key"] == c["key"] else ""}" href="{o["file"]}">{o["name"]} ({o["n"]})</a>'
        for o in CATS.values())
    scissor = c["key"] in ("es", "rt")
    head = "<th>Model</th><th>Working height</th>" + ("<th>Platform height</th>" if scissor else "<th>Outreach</th>") + "<th>Capacity</th><th>Machine weight</th><th>Power</th>"
    trs = "".join(
        f'<tr><td><a href="rent-{r[0]}.html"><strong>{r[1]}</strong></a></td><td>{r[4]:g} m</td><td>{(r[5] if scissor else r[6]):g} m</td><td>{r[7]} kg</td><td>{r[8]:,} kg</td><td>{r[9]}</td></tr>'
        for r in sorted(ms, key=lambda r: r[4]))
    others = "".join(f'<a class="chip" href="{o["file"]}">{o["name"]}</a>' for o in CATS.values() if o["key"] != c["key"])
    choose = "".join(f"<p><strong>{t}:</strong> {x}</p>" for t, x in c["choose"])
    intro = c["intro"].format(n=c["n"], lo=c["lo"], hi=c["hi"])
    return f'''<!-- 1. COMPACT HEADER: H1 + answer-first intro + category switcher (listing comes first on this page) -->
<section class="r-hero r-hero--compact">
  {hero_img(c["img"], c["one"] + " for rent in Dubai")}
  <div class="wrap r-hero-inner">
    <div class="listing-hero-grid">
      <div>
        <h1>{c["h1"]}</h1>
        <p class="lead">{intro}</p>
      </div>
      <div class="listing-hero-cta">
        <a class="btn btn--red btn--block" href="contact.html#enquiry">Get a Quote</a>
        <a class="btn btn--wa btn--block" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp</a>
      </div>
    </div>
    <nav class="cat-chips" aria-label="Rental categories">{switch}</nav>
  </div>
</section>

<!-- 2. LISTING with category-specific filters (filter URLs = noindex in WordPress) -->
<section class="section" style="padding-top:32px">
  <div class="wrap listing">
    {sidebar(groups, c["n"], "machines")}
    <div>
      {listing_bar(c["n"], "machines", [("height-asc", "Working height (low to high)"), ("height-desc", "Working height (high to low)"), ("cap-desc", "Capacity (highest first)")])}
      <div class="grid grid-3" data-listing data-noun="machines">
        {"".join(items)}
      </div>
      {EMPTY}
    </div>
  </div>
</section>

<!-- 3. COMPARE TABLE (from your live Equipment Hire data) -->
<section class="section section--alt">
  <div class="wrap">
    <div class="section-head"><h2>Compare {c["one"]} Models</h2></div>
    <div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{trs}</tbody></table></div>
  </div>
</section>

<!-- 4 + 5. BEST USES and HOW TO CHOOSE -->
<section class="section">
  <div class="wrap grid grid-2" style="gap:56px;align-items:start">
    <div class="content">
      <h2>Best Uses for {c["name"]}</h2>
      <ul class="tick-list">{"".join(f"<li>{u}</li>" for u in c["uses"])}</ul>
      {media(c["img"] + "-sm", c["one"] + " at work", "ratio-16-9")}
    </div>
    <div class="content">
      <h2>How to Choose the Right {c["one"]}</h2>
      {choose}
    </div>
  </div>
</section>

<!-- 6. RENTAL OPTIONS -->
<section class="section section--alt section--tight">
  <div class="wrap">
    <h2>Rental Options</h2>
    <div class="grid grid-4 mt-24">
      <div class="service-block"><div class="icon">{icon("calendar")}</div><h3>Flexible periods</h3><p>Daily, weekly, monthly or long-term hire.</p></div>
      <div class="service-block"><div class="icon">{icon("truck")}</div><h3>Delivery across the UAE</h3><p>To your site in all seven emirates, as soon as possible.</p></div>
      <div class="service-block"><div class="icon">{icon("user")}</div><h3>Operator on request</h3><p>Ask for an operator when you book.</p></div>
      <div class="service-block"><div class="icon">{icon("shield")}</div><h3>Inspected machines</h3><p>Every machine is checked before delivery.</p></div>
    </div>
  </div>
</section>

<!-- 7. FAQ -->
<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Questions</span><h2>{c["one"]} Rental Questions</h2></div>
    {faq_html(c["faq"])}
  </div>
</section>

<!-- 8. RELATED: internal links to other categories, landing page and guides -->
<section class="section section--alt section--tight">
  <div class="wrap grid grid-2" style="gap:40px">
    <div>
      <h2 style="font-size:1.5rem">Other Rental Machines</h2>
      <div class="cat-chips">{others}<a class="chip" href="rental.html">All rental equipment</a></div>
    </div>
    <div>
      <h2 style="font-size:1.5rem">Related Guides</h2>
      <ul class="tick-list mt-24">
        <li><a href="blog-detail.html">Boom Lift vs Scissor Lift: How to Choose</a></li>
        <li><a href="blog-detail.html">Working Height vs Platform Height Explained</a></li>
      </ul>
    </div>
  </div>
</section>

{{{{cta:Get a Quote for {c["one"].lower().replace("lift", "lift")}s|Tell us the working height, site location and dates. We'll confirm the right model and send your quote.}}}}
'''


# ================================================================== SALES LANDING
def page_sales_landing():
    by_t = Counter(TYPES[s[4]][0] for s in SALE)
    sold_t = Counter(TYPES[s["t"]][0] for s in SOLD)
    to = Counter(s["to"] for s in SOLD if s["to"])
    models = Counter(s["model"] for s in SOLD).most_common(4)
    dated = sorted([s for s in SOLD if s["date"] and not s["date"].endswith("-00")], key=lambda s: s["date"], reverse=True)
    first = min(s["date"] for s in SOLD if s["date"])
    recent = "".join(
        f'<tr><td><a href="sold-{s["id"]}.html"><strong>{s["model"]}</strong></a></td><td>{TYPES[s["t"]][1]}</td><td>{s["year"]}</td><td>{s["origin"]}</td><td>{s["to"]}</td><td>{fmt_date(s["date"])}</td></tr>'
        for s in dated[:6])
    cats = [
        ("telescopic", "Telescopic Boom Lifts", "s-860sj-2004-sm", "JLG 660SJ, 860SJ, 1200SJP, 1350SJP and Genie S-65 booms."),
        ("articulated", "Articulated Boom Lifts", "s-600aj-1-sm", "JLG 600AJ and electric E450AJ / M450AJ booms."),
        ("scissor", "Scissor Lifts", "cat-rt-scissor-sm", "Genie GS-4047 and GS-5390 RT scissors – sourced on request."),
    ]
    tiles = []
    for v, name, img, txt in cats:
        avail = by_t.get(v, 0)
        # used and sold listings both filter by category slug (same values as the home finder); commas tick several boxes
        sold_cats = ",".join(TYPE_CAT[k] for k, (tv, _) in TYPES.items() if tv == v)
        href = f"sales-used.html#category-{v}-boom-lifts" if avail else f"sales-sold.html#category-{sold_cats}"
        meta = f"{avail} available · {sold_t.get(v, 0)} sold" if avail else f"{sold_t.get(v, 0)} sold · sourced on request"
        tiles.append(f'''<a class="tile" href="{href}">
        {media(img, "Used " + name.lower() + " for sale", "tile-img")}
        <div class="tile-body">
          <span class="tile-meta">{meta}</span>
          <h3>{name}</h3>
          <p>{txt}</p>
          <span class="tile-link">{"See available machines" if avail else "See sales records"} →</span>
        </div>
      </a>''')
    faq = [
        ("Do you export used access equipment?", f"Yes. Our sales records show {N_SOLD} machines sold since {fmt_date(first)}, mostly exported to buyers in India and Vietnam."),
        ("Can I see the machine before I buy?", "Ask us for detailed photos or a walk-around video of the exact machine. [Add: inspection options and where machines are located.]"),
        ("Can you find a machine that is not listed?", "Yes. Tell us the model, year range and working height you need, and we will source it for you."),
        ("Are prices shown on the website?", "Prices change with stock and shipping, so we quote on request. Send an enquiry or WhatsApp us for a price."),
    ]
    mtxt = ", ".join(m for m, _ in models)
    return f'''<!-- 1. HERO: full-width photo background (LCP, eager), same as Rental -->
<section class="r-hero">
  {hero_img("s-1350sjp-2", "Used JLG 1350SJP telescopic boom lift for sale")}
  <div class="wrap r-hero-inner">
    <span class="eyebrow">Used equipment sales</span>
    <h1>Used Boom Lifts &amp; Scissor Lifts for Sale – UAE &amp; Export</h1>
    <p class="hero-lead">Cherry Pickers Equipment buys and sells used access equipment from JLG and Genie. We have {len(SALE)} machines available now and have sold {N_SOLD} machines since {fmt_date(first)}, mostly to buyers in India and Vietnam.</p>
    <div class="hero-actions">
      <a class="btn btn--red" href="sales-used.html">View Used Equipment</a>
      <a class="btn btn--wa" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp Sales</a>
    </div>
  </div>
</section>

<!-- 2. THREE PATHS: new, used stock and sold records -->
<section class="section section--tight">
  <div class="wrap grid grid-3 paths-3">
    <a class="path-card" href="sales-new.html">
      <span class="path-num{"" if NEW else " path-num--text"}">{len(NEW) if NEW else "On request"}</span>
      <div><h2>New Equipment</h2><p>Brand-new machines for sale. Tell us the model you need for price and delivery time.</p><span class="link-arrow">Browse new equipment →</span></div>
    </a>
    <a class="path-card" href="sales-used.html">
      <span class="path-num">{len(SALE)}</span>
      <div><h2>Used Equipment</h2><p>Machines in stock with year, origin and photos. Filter by type, brand and year.</p><span class="link-arrow">Browse used equipment →</span></div>
    </a>
    <a class="path-card path-card--navy" href="sales-sold.html">
      <span class="path-num">{N_SOLD}</span>
      <div><h2>Sold Equipment</h2><p>Every machine we have sold – model, year, origin, destination and month.</p><span class="link-arrow">See sold records →</span></div>
    </a>
  </div>
</section>

<!-- 3. CATEGORY TILES: link to filtered listings -->
<section class="section section--alt">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Shop by type</span><h2>Used Access Equipment by Category</h2></div>
    <div class="tiles tiles--3">{"".join(tiles)}</div>
  </div>
</section>

<!-- 4. WHY BUY FROM US -->
<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Why buy from us</span><h2>Why Buyers Choose Cherry Pickers Equipment</h2></div>
    <div class="grid grid-3" style="gap:32px">
      <div class="why-item"><div class="tick">{icon("globe")}</div><div><h3>Sourced worldwide</h3><p>Machines from Australia, Europe, the USA and Asia.</p></div></div>
      <div class="why-item"><div class="tick">{icon("file")}</div><div><h3>Full details on every machine</h3><p>Year, origin and photos – and a walk-around video on request.</p></div></div>
      <div class="why-item"><div class="tick">{icon("truck")}</div><div><h3>Export experience</h3><p>{N_SOLD} machines sold, with regular shipments to India and Vietnam.</p></div></div>
      <div class="why-item"><div class="tick">{icon("wrench")}</div><div><h3>Our own workshop</h3><p>The team that maintains our rental fleet knows these machines.</p></div></div>
      <div class="why-item"><div class="tick">{icon("tag")}</div><div><h3>Popular models</h3><p>Most traded: {mtxt}.</p></div></div>
      <div class="why-item"><div class="tick">{icon("phone")}</div><div><h3>Fast answers</h3><p>WhatsApp us the model you need for price and availability.</p></div></div>
    </div>
  </div>
</section>

<!-- 5. RECENTLY SOLD (real records) -->
<section class="section section--alt">
  <div class="wrap">
    <div class="flex-between section-head" style="max-width:none">
      <div><span class="eyebrow">Track record</span><h2>Recently Sold</h2></div>
      <a class="link-arrow" href="sales-sold.html">All {N_SOLD} sold records →</a>
    </div>
    <div class="table-wrap"><table>
      <thead><tr><th>Machine</th><th>Type</th><th>Year</th><th>Origin</th><th>Sold to</th><th>Month</th></tr></thead>
      <tbody>{recent}</tbody>
    </table></div>
  </div>
</section>

<!-- 6. HOW BUYING WORKS -->
<section class="section">
  <div class="wrap">
    <div class="section-head section-head--center"><span class="eyebrow">Buying from us</span><h2>How Buying a Used Machine Works</h2></div>
    <div class="grid grid-4 steps">
      <div class="step"><h3>Send an enquiry</h3><p>Tell us the machine you want, or ask us to source one.</p></div>
      <div class="step"><h3>Photos &amp; video</h3><p>Get detailed photos or a walk-around video of the machine.</p></div>
      <div class="step"><h3>Agree price &amp; pay</h3><p>We confirm price, payment terms and documents.</p></div>
      <div class="step"><h3>Delivery or export</h3><p>Delivered in the UAE, or prepared for shipping abroad.</p></div>
    </div>
  </div>
</section>

<!-- 7. FAQ -->
<section class="section section--alt">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Questions</span><h2>Buying Used Access Equipment – Questions</h2></div>
    {faq_html(faq)}
  </div>
</section>

{{{{cta:Looking for a Specific Machine?|Tell us the model, year or working height you need. We source used boom lifts and scissor lifts worldwide.}}}}
'''


def sales_tabs(active):
    def cls(k):
        return ' class="active"' if active == k else ""
    return f'''<nav class="tabs" aria-label="Sales">
      <a{cls("new")} href="sales-new.html">New <span class="count">{len(NEW)}</span></a>
      <a{cls("used")} href="sales-used.html">Used <span class="count">{len(SALE)}</span></a>
      <a{cls("sold")} href="sales-sold.html">Sold <span class="count">{N_SOLD}</span></a>
    </nav>'''


def sales_hero(h1, lead, img, alt, extra=""):
    return f'''<section class="r-hero r-hero--compact">
  {hero_img(img, alt)}
  <div class="wrap r-hero-inner">
    <div class="listing-hero-grid">
      <div>
        <h1>{h1}</h1>
        <p class="lead">{lead}</p>
      </div>
      <div class="listing-hero-cta">
        <a class="btn btn--red btn--block" href="contact.html#enquiry">Send an Enquiry</a>
        <a class="btn btn--wa btn--block" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp Sales</a>
      </div>
    </div>
    {extra}
  </div>
</section>'''


def sale_listing(rows, note=""):
    """Sidebar + listing bar + sale cards for a list of SALE-format tuples."""
    ybands = [(2015, 2100, "2015 and newer"), (2008, 2015, "2008 – 2014"), (0, 2008, "2007 and older")]
    hbands = [(0, 20, "Up to 20 m"), (20, 30, "20 – 30 m"), (30, 99, "30 m and above")]
    ft, fb, fy, fh, fo = Counter(), Counter(), Counter(), Counter(), Counter()
    items = []
    for s in sorted(rows, key=lambda s: -s[1]):
        tv = TYPE_CAT[s[4]]; bv = slug(s[3]); yv, _ = band(s[1], ybands); hv, _ = band(s[6], hbands); ov = slug(s[5])
        ft[tv] += 1; fb[bv] += 1; fy[yv] += 1; fh[hv] += 1; fo[ov] += 1
        items.append(sale_card(s[0], f"category={tv} brand={bv} year={yv} height={hv} origin={ov}"))
    origins = sorted({s[5] for s in rows})
    groups = [
        filter_group("Machine type", "category", [(c["slug"], c["one"], ft[c["slug"]]) for c in CATS.values() if ft[c["slug"]]]),
        filter_group("Brand", "brand", [("jlg", "JLG", fb["jlg"]), ("genie", "Genie", fb["genie"])]),
        filter_group("Year", "year", [(slug(l), l, fy[slug(l)]) for _, _, l in ybands]),
        filter_group("Working height", "height", [(slug(l), l, fh[slug(l)]) for _, _, l in hbands]),
        filter_group("Machine origin", "origin", [(slug(o), o, fo[slug(o)]) for o in origins]),
    ]
    n = len(rows)
    return f'''<div class="listing">
      {sidebar(groups, n, "machines")}
      <div>
        {listing_bar(n, "machines", [("year-desc", "Year (newest first)"), ("year-asc", "Year (oldest first)"), ("height-desc", "Working height (highest first)")])}
        <div class="grid grid-3" data-listing data-noun="machines">
          {"".join(items)}
        </div>
        {EMPTY}
        {note}
      </div>
    </div>'''


# ================================================================== SALES NEW
def page_sales_new():
    if NEW:
        body = sale_listing(NEW)
        lead = f"{len(NEW)} new machines for sale. Contact us for price and delivery time."
    else:
        lead = "Brand-new boom lifts and scissor lifts supplied on request. Tell us the machine you need and we'll send price and delivery time."
        body = f'''<div class="split-panel" style="max-width:760px;margin:24px auto;text-align:center">
      <h2>New Equipment on Request</h2>
      <p>Tell us the machine you need and we'll send price and delivery time. [Confirm which brands you sell new.]</p>
      <div class="hero-actions" style="justify-content:center">
        <a class="btn btn--red" href="contact.html#enquiry">Send an Enquiry</a>
        <a class="btn btn--wa" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp</a>
      </div>
      <p class="mt-24"><a class="link-arrow" href="sales-used.html">Browse Used Equipment →</a></p>
    </div>'''
    return f'''{sales_hero("New Access Equipment for Sale", lead, "cat-electric-scissor", "New electric scissor lift for sale in the UAE")}

<section class="section" style="padding-top:28px">
  <div class="wrap">
    {sales_tabs("new")}
    {body}
  </div>
</section>

{{{{cta:Looking for a Specific Machine?|Tell us the model, working height and delivery location. We'll send price and delivery time.}}}}
'''


# ================================================================== SALES USED
def page_sales_used():
    note = f'<p class="small muted mt-24">Mockup shows page 1 of your current listing ({len(SALE)} machines – one duplicate listing merged). Grey cards = no reliable photo yet.</p>'
    return f'''{sales_hero("Used Access Equipment for Sale", f"{len(SALE)} used boom lifts in stock from JLG and Genie, with year, origin and photos. Contact us for price, more photos or a walk-around video.", "s-600aj-1", "Used JLG 600AJ articulated boom lift for sale")}

<section class="section" style="padding-top:28px">
  <div class="wrap">
    {sales_tabs("used")}
    {sale_listing(SALE, note)}
  </div>
</section>

<section class="section section--alt section--tight">
  <div class="wrap flex-between" style="align-items:center">
    <div style="max-width:700px">
      <h2 style="margin-bottom:6px">See What We Have Sold</h2>
      <p class="muted" style="margin:0">{N_SOLD} machines sold and exported – browse the full record by model, year and destination.</p>
    </div>
    <a class="btn btn--navy" href="sales-sold.html">View Sold Records</a>
  </div>
</section>

{{{{cta:Looking for a Specific Machine?|Tell us the model, year or working height you need. We source used boom lifts and scissor lifts worldwide.}}}}
'''


# ================================================================== SALES SOLD
def page_sales_sold():
    """Sold records: same layout as Used (sidebar filters + listing bar + machine cards), 12 cards per 'Show more'."""
    ybands = [(2016, 2100, "2016 and newer"), (2011, 2016, "2011 – 2015"), (2006, 2011, "2006 – 2010"), (0, 2006, "2005 and older")]
    ft, fb, fy, fo, fto, fys = Counter(), Counter(), Counter(), Counter(), Counter(), Counter()
    items = []
    for s in sorted(SOLD, key=lambda s: s["date"] or "0000", reverse=True):
        tv = TYPE_CAT[s["t"]]
        bv = slug(s["model"].split()[0])
        yv, _ = band(s["year"], ybands)
        ov = slug(s["origin"])
        tov = slug(s["to"]) if s["to"] else "not-recorded"
        ysv = s["date"][:4] if s["date"] else "not-recorded"
        ft[tv] += 1; fb[bv] += 1; fy[yv] += 1; fo[ov] += 1; fto[tov] += 1; fys[ysv] += 1
        items.append(sold_card(s, f"category={tv} brand={bv} year={yv} origin={ov} to={tov} sold={ysv}"))
    first = min(s["date"] for s in SOLD if s["date"])
    top = Counter(s["model"] for s in SOLD).most_common(1)[0]
    origins = [o for o, _ in Counter(s["origin"] for s in SOLD).most_common()]
    dests = [d for d, _ in Counter(s["to"] for s in SOLD if s["to"]).most_common()]
    years = sorted({k for k in fys if k != "not-recorded"}, reverse=True) + ["not-recorded"]
    groups = [
        filter_group("Machine type", "category", [(c["slug"], c["one"], ft[c["slug"]]) for c in CATS.values() if ft[c["slug"]]]),
        filter_group("Brand", "brand", [("jlg", "JLG", fb["jlg"]), ("genie", "Genie", fb["genie"])]),
        filter_group("Sold to", "to", [(slug(d), d, fto[slug(d)]) for d in dests] + ([("not-recorded", "Not recorded", fto["not-recorded"])] if fto["not-recorded"] else [])),
        filter_group("Year sold", "sold", [(y, y if y != "not-recorded" else "Not recorded", fys[y]) for y in years if fys[y]]),
        filter_group("Model year", "year", [(slug(l), l, fy[slug(l)]) for _, _, l in ybands]),
        filter_group("Machine origin", "origin", [(slug(o), o, fo[slug(o)]) for o in origins]),
    ]
    stats = f'''<div class="sold-stats">
      <div><strong>{N_SOLD}</strong><span>Machines sold</span></div>
      <div><strong>{fto["india"]}</strong><span>To India</span></div>
      <div><strong>{fto["vietnam"]}</strong><span>To Vietnam</span></div>
      <div><strong>{top[0]}</strong><span>Most sold model ({top[1]})</span></div>
    </div>'''
    lead = (f"A record of every used boom lift and scissor lift we have sold: {N_SOLD} machines since {fmt_date(first)}, "
            f"exported mainly to India ({fto['india']}) and Vietnam ({fto['vietnam']}). Looking for one like these? We can source it.")
    note = '<p class="small muted mt-24">Photos are model photos from our rental fleet and sales stock, not the sold unit. Grey cards = no photo of that model yet.</p>'
    return f'''{sales_hero("Sold Access Equipment – Our Sales Records", lead, "s-600aj-2", "Used JLG boom lift sold and exported", stats)}

<section class="section" style="padding-top:28px">
  <div class="wrap">
    {sales_tabs("sold")}
    <div class="listing">
      {sidebar(groups, N_SOLD, "records")}
      <div>
        {listing_bar(N_SOLD, "records", [("date-desc", "Most recently sold"), ("date-asc", "Oldest sales first"), ("year-desc", "Model year (newest first)"), ("year-asc", "Model year (oldest first)")])}
        <div class="grid grid-3" data-listing data-page-size="12" data-noun="records">
          {"".join(items)}
        </div>
        {EMPTY.replace("No machines match", "No records match")}
        <div class="center mt-24"><button class="btn btn--ghost" data-more>Show more records</button></div>
        {note}
      </div>
    </div>
  </div>
</section>

<section class="section section--alt section--tight">
  <div class="wrap flex-between" style="align-items:center">
    <div style="max-width:700px">
      <h2 style="margin-bottom:6px">Looking for One Available Now?</h2>
      <p class="muted" style="margin:0">{len(SALE)} used boom lifts in stock with year, origin and photos – ready for UAE delivery or export.</p>
    </div>
    <a class="btn btn--navy" href="sales-used.html">View Used Equipment</a>
  </div>
</section>

{{{{cta:Want a Machine Like These?|Tell us the model and year range you need. We source used JLG and Genie machines worldwide.}}}}
'''


# ================================================================== SOLD DETAIL (one record) – same layout as the used-sale detail page
def page_sold_detail(s):
    y, m, origin = s["year"], s["model"], s["origin"]
    tname = TYPES[s["t"]][1]
    cat = SLUG_CAT[TYPE_CAT[s["t"]]]
    sold = fmt_date(s["date"])
    to = s["to"] or "Not recorded"
    same = [x for x in SOLD if x["model"] == m]
    rent = MODEL_RENT.get(m)
    wh = MODEL_WH.get(m)

    # sale record + model specs (only specs we already hold for this model; client fills the rest)
    record = [("Make / model", m), ("Brand", m.split()[0]), ("Type", tname), ("Model year", y), ("Machine origin", origin),
              ("Sold to", to), ("Date sold", sold), ("Status", '<span class="badge badge--sold">Sold</span>')]
    rec_rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in record)
    if rent:
        _, _, _, _, rwh, rph, rout, rcap, rwt, rpw, _, _ = rent
        spec = [("Working height", f"{rwh:g} m"), ("Platform height", f"{rph:g} m") if rph else ("Horizontal outreach", f"{rout:g} m"),
                ("Safe working load", f"{rcap} kg"), ("Machine weight", f"{rwt:,} kg"), ("Power", rpw)]
        spec_src = f"Model specs from our rental fleet data for the {m} – not measured on this unit."
    elif wh:
        spec = [("Working height", f"{wh:g} m"), ("Horizontal outreach", "[from spec sheet]"), ("Safe working load", "[from spec sheet]")]
        spec_src = "Working height from our sales stock data. [Add the other specs from the manufacturer spec sheet.]"
    else:
        spec = [("Working height", "[from spec sheet]"), ("Safe working load", "[from spec sheet]")]
        spec_src = "[Add the main specs from the manufacturer spec sheet.]"
    spec_rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in spec)

    # similar: used stock of the same type (same model first), then other sold records of this model
    avail = sorted((x for x in SALE if x[4] == s["t"]), key=lambda x: (x[2] != m, -x[1]))[:3]
    if len(avail) < 3:
        avail += sorted((x for x in SALE if x[4] != s["t"]), key=lambda x: -x[1])[:3 - len(avail)]
    others = sorted((x for x in same if x is not s), key=lambda x: x["date"] or "0000", reverse=True)[:3]
    others_html = "" if not others else f'''
<section class="section section--alt section--tight">
  <div class="wrap">
    <div class="flex-between section-head" style="max-width:none"><h2 class="mt-0">Other {m} Machines We Have Sold</h2><a class="link-arrow" href="sales-sold.html">All {N_SOLD} sold records →</a></div>
    <div class="grid grid-3">
      {"".join(sold_card(x) for x in others)}
    </div>
  </div>
</section>'''
    where = f" and exported to {s['to']}" if s["to"] else ""
    when = f" in {sold}" if s["date"] else ""
    rent_link = (f'<p class="mt-24"><a class="link-arrow" href="rent-{rent[0]}.html">Need a {m} for a short job? Rent one from our fleet →</a></p>'
                 if rent else "")
    return f'''<section>
  <div class="wrap">
    <!-- SOLD BANNER: the page stays live after the sale (keeps its search traffic) and points buyers to similar machines -->
    <div class="sold-banner">
      <span><strong>This machine has been sold.</strong> Looking for a {m}? See machines available now, or ask us to source one.</span>
      <a class="btn btn--red btn--sm" href="sales-used.html#category-{cat["slug"]}">See available machines</a>
    </div>
  </div>
  <div class="wrap detail-top">
    <div class="gallery">
      {sold_pic(s, "gallery-main", eager=True, label="Model photo – not the sold unit")}
      <p class="small muted" style="margin-top:8px">Photo shows the model, not the sold unit. Ask us for photos of machines available now.</p>
    </div>
    <div class="detail-info">
      <span class="badge badge--sold">Sold</span>
      <h1>{y} {m} {tname} – Sold</h1>
      <p class="stock-no">Sold <strong>{sold}</strong> · Sold to: <strong>{to}</strong> · Machine origin: {origin}</p>
      <div class="key-specs">
        <div><strong>{y}</strong>Year</div>
        <div><strong>{origin}</strong>Origin</div>
        <div><strong>{to}</strong>Sold to</div>
        <div><strong>{sold}</strong>Sold</div>
      </div>
      <div class="price" style="font-size:1.6rem;margin-bottom:16px">No longer available <small>We can source a similar {m} – UAE and export enquiries welcome</small></div>
      <div class="detail-actions">
        <a class="btn btn--red btn--block" href="contact.html#enquiry">Find Me a Similar Machine</a>
        <div class="row">
          <a class="btn btn--wa" href="{{{{WA_LINK}}}}" style="justify-content:center">{icon("wa")} WhatsApp</a>
          <a class="btn btn--navy" href="{{{{PHONE_LINK}}}}" style="justify-content:center">{icon("phone")} Call</a>
        </div>
      </div>
      <div class="assure">
        <ul>
          <li>We have sold {len(same)} {m} machine{"s" if len(same) != 1 else ""}</li>
          <li>{N_SOLD} machines sold, mostly to India and Vietnam</li>
          <li>Used JLG and Genie machines sourced worldwide</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section section--alt" style="padding-top:56px">
  <div class="wrap two-col">
    <div class="content">
      <h2>About This Sale</h2>
      <p>This {y} {m} {tname.lower()} (machine origin: {origin}) was sold by Cherry Pickers Equipment{when}{where}. It is one of {len(same)} {m} machines in our sales records. Need one like it? Tell us the year range and destination and we will find a matching machine.</p>

      <h2>Sale Record</h2>
      <div class="table-wrap"><table class="spec-table"><tbody>{rec_rows}</tbody></table></div>

      <h2>{m} Specifications</h2>
      <div class="table-wrap"><table class="spec-table"><tbody>{spec_rows}</tbody></table></div>
      <p class="small muted">{spec_src}</p>
      {rent_link}

      <h2>How We Source a Machine Like This</h2>
      <ul class="tick-list">
        <li>Tell us the model, year range and destination country</li>
        <li>We find matching machines and send photos, year and origin</li>
        <li>Agree price, payment terms and documents</li>
        <li>Delivered in the UAE, or prepared for shipping abroad</li>
      </ul>
    </div>
    <aside class="side-box">
      <h3>Find me a {m}</h3>
      <p class="small muted">Similar to this {y} unit · {tname}</p>
      <form data-mock>
        <div class="form-grid" style="grid-template-columns:1fr">
          <div class="field"><label>Name <span class="req">*</span></label><input required></div>
          <div class="field"><label>Phone / WhatsApp <span class="req">*</span></label><input required></div>
          <div class="field"><label>Year range</label><input placeholder="e.g. {y - 2} – {y + 3}"></div>
          <div class="field"><label>Country</label><input placeholder="UAE or export country"></div>
          <button class="btn btn--red btn--block" type="submit">Send request</button>
        </div>
        <div class="form-ok">Thanks – this is a mockup, nothing was sent.</div>
      </form>
    </aside>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="flex-between section-head" style="max-width:none"><h2 class="mt-0">Similar Machines Available Now</h2><a class="link-arrow" href="sales-used.html">All used equipment →</a></div>
    <div class="grid grid-3">
      {"".join(sale_card(x[0]) for x in avail)}
    </div>
  </div>
</section>
{others_html}

{{{{cta:Want a {m} Like This One?|Tell us the year range and where it needs to go. We source used JLG and Genie machines worldwide.}}}}
'''


# ------------------------------------------------------------------ header / footer
def header(active):
    def cur(name):
        return ' aria-current="page"' if name == active else ""
    # Same menu items and links as the home page header (HOME_NAV), in this header's own markup/styles.
    def item(n, u, sub):
        key = n.lower()
        if not sub:
            return f'<li><a href="{u}"{cur(key)}>{n}</a></li>'
        drop = "".join(f'<li><a href="{su}">{sn}{f"<small>{ss}</small>" if ss else ""}</a></li>' for sn, su, ss in sub)
        return f'<li class="has-drop"><a href="{u}"{cur(key)}>{n}</a>\n          <ul class="drop">{drop}</ul>\n        </li>'
    menu = "\n        ".join(item(n, u, sub) for n, u, sub in HOME_NAV)
    return f'''<div class="mock-note">UI mockup for review · real photos and data from your website · grey boxes = photos still needed</div>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="index.html">
      <img src="assets/img/logo.webp" alt="Cherry Pickers Equipment – The Right Pick for Every Height" width="1024" height="340" class="logo-img">
    </a>
    <nav class="main-nav" aria-label="Main">
      <ul>
        {menu}
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


SOCIAL = [
    ("Facebook", "fb", "https://www.facebook.com/cherrypickersequipmentdubai/"),
    ("Instagram", "ig", "https://www.instagram.com/cherrypickersequipment_uae/"),
    ("LinkedIn", "li", "https://www.linkedin.com/company/cherry-pickers-equipment/"),
    ("YouTube", "yt", "https://www.youtube.com/@CherryPickersEquipmentRentals"),
    ("TikTok", "tt", "https://www.tiktok.com/@cherrypickersrentaldubai"),
    ("Pinterest", "pinterest", "https://www.pinterest.com/cherrypickersrentaldubai/"),
]


def footer():
    cat_links = "".join(f'<li><a href="{c["file"]}">{c["name"]}</a></li>' for c in CATS.values())
    social = "".join(f'\n        <a href="{u}" aria-label="{n}" target="_blank" rel="noopener">{icon(k)}</a>' for n, k, u in SOCIAL)
    return f'''<footer class="site-footer">
  <div class="wrap footer-grid">
    <div class="footer-about">
      <a class="logo logo--footer" href="index.html"><img src="assets/img/logo.webp" alt="Cherry Pickers Equipment" width="1024" height="340" loading="lazy" class="logo-img"></a>
      <p>Boom lift and scissor lift rental across all seven UAE emirates, with maintenance and used equipment sales.</p>
      <div class="social">{social}
      </div>
    </div>
    <div>
      <h3>Rental</h3>
      <ul>{cat_links}<li><a href="rental.html">Rental overview</a></li></ul>
    </div>
    <div>
      <h3>Company</h3>
      <ul>
        <li><a href="about.html">About us</a></li>
        <li><a href="services.html">Services</a></li>
        <li><a href="maintenance-repair.html">Maintenance &amp; Repair</a></li>
        <li><a href="services-amc.html">AMC</a></li>
        <li><a href="services-on-site-repairs.html">On-site Repairs</a></li>
        <li><a href="services-workshop.html">Workshop Services</a></li>
        <li><a href="sales.html">Sales</a></li>
        <li><a href="sales-new.html">New Equipment</a></li>
        <li><a href="sales-used.html">Used Equipment</a></li>
        <li><a href="sales-sold.html">Sold Equipment</a></li>
        <li><a href="blog.html">Blog</a></li>
        <li><a href="contact.html">Contact</a></li>
      </ul>
    </div>
    <div>
      <h3>Contact</h3>
      <ul class="footer-contact">
        <li>{icon("pin")}<span>{ADDRESS}</span></li>
        <li>{icon("phone")}<a href="{PHONE_LINK}">{PHONE}</a></li>
        <li>{icon("mail")}<a href="mailto:info@cherrypickersglobal.com">info@cherrypickersglobal.com</a></li>
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
  <a class="quote" href="contact.html#enquiry">{icon("quote")}Get a Quote</a>
</nav>'''


# ================================================================== HOME PAGE (v3, mobile-first, own stylesheet home.css)
# TODO: set the real Google Business Profile links before launch.
#   GOOGLE_REVIEWS_URL      -> the "Reviews" link of the Google Business Profile (e.g. https://g.page/r/<id>)
#   GOOGLE_WRITE_REVIEW_URL -> Business Profile > "Ask for reviews" link (e.g. https://g.page/r/<id>/review)
# Until then both open a Google Maps search for the business (never "#").
GOOGLE_REVIEWS_URL = "https://www.google.com/maps/search/?api=1&amp;query=" + quote("Cherry Pickers Equipment Dubai Industrial City")
GOOGLE_WRITE_REVIEW_URL = GOOGLE_REVIEWS_URL
BREAKDOWN = "+971 56 801 9344"
BREAKDOWN_LINK = "tel:+971568019344"
HOME_FONTS = "https://fonts.googleapis.com/css2?family=Barlow:wght@500;600;700;800&family=Manrope:wght@400;500;600;700&display=swap"
SITE_FONTS = "https://fonts.googleapis.com/css2?family=Barlow:wght@600;700;800&family=Manrope:wght@400;500;600;700&display=swap"
CARET = '<svg class="caret" viewBox="0 0 10 10" aria-hidden="true"><path d="M1 3l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
TICK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'

# TODO: sample hour-meter readings from the v3 design – replace with the real hours before launch.
HOURS = {"a13": "7,850", "a4": "2,140", "a1": "6,320", "a8": "8,900"}

# Home FAQ: one list feeds both the <details> accordion and the FAQPage JSON-LD in <head>.
HOME_FAQ = [
    ("What access equipment can I rent from you?", "We rent 30 models of electric and rough terrain scissor lifts and electric, articulated and telescopic boom lifts, from 7.8 m to 43 m working height."),
    ("What is the minimum rental period?", "We rent for short projects and long contracts – from a few days to several weeks or longer. Share your dates and we'll quote for that period."),
    ("Do you deliver outside Dubai?", "Yes – we deliver and collect across all seven emirates, as soon as possible."),
    ("Do you supply operators?", "Yes, operators are available on request – mention it when you ask for a quote. If your own team operates the machine, they need recognised training such as an IPAF PAL card."),
    ("What do I get with a rental machine?", f"A maintained machine inspected before hire, with both platform and ground controls, delivery and collection arranged by our team, and 24/7 breakdown support on {BREAKDOWN}."),
    ("Which brands do you rent and sell?", "JLG, Genie and Dingli are our core brands, along with Haulotte, Snorkel, Nifty and Sinoboom."),
    ("Can you service machines that we own?", "Yes – we offer AMC (annual maintenance contracts), on-site repairs and workshop services for boom lifts and scissor lifts."),
    ("Can I check a used machine before buying?", "Yes. Every listing shows the year, origin, specs and condition photos, and you can ask for inspection reports and documents before you buy."),
    ("Can you export a machine to my country?", "Yes. We handle packing, logistics and shipping documents – 750+ machines have gone to India and 100+ to Vietnam so far."),
]


def home_faq_html():
    return "\n".join(
        f'      <details class="qa"{" open" if n == 0 else ""}><summary>{q}</summary><p>{a}</p></details>'
        for n, (q, a) in enumerate(HOME_FAQ))


def home_faq_jsonld():
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in HOME_FAQ]}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"


def home_rcard(key):
    """Home 'Fast-moving rental machines' card. Title + Details -> the machine's own page."""
    k, m, brand, cat, wh, ph, out, cap, wt, pw, img, st = RENTAL[key]
    c = CATS[cat]
    mid = (f"<div><strong>{ph:g} m</strong><span>Platform ht.</span></div>" if ph
           else f"<div><strong>{out:g} m</strong><span>Outreach</span></div>")
    pill = '<span class="pill avail">Available</span>' if st == "ok" else '<span class="pill busy">On hire – ask for date</span>'
    return f'''<article class="mc">
        <div class="mc-img">{img_tag(img + "-sm", f"{m} for rent in Dubai")}{pill}</div>
        <div class="mc-body">
          <h3><a href="rent-{k}.html">{m}</a></h3>
          <div class="type">{c['one']} · {pw}</div>
          <div class="specs"><div><strong>{wh:g} m</strong><span>Working ht.</span></div>{mid}<div><strong>{cap} kg</strong><span>Capacity</span></div></div>
          <div class="mc-btns">
            <a class="btn btn-out btn-sm" href="rent-{k}.html">Details</a>
            <a class="btn btn-red btn-sm" href="#enquiry" data-want="rent">Get a Quote</a>
            <a class="btn btn-wa btn-icon" href="{wa_url(f"Hi, I need a quote for the {m}.")}" target="_blank" rel="noopener" aria-label="WhatsApp about {m}">{WA_SVG}</a>
          </div>
        </div>
      </article>'''


def home_scard(sid):
    """Home 'High-demand used equipment' card. Photo + title -> the machine's own page under sales/used/."""
    i, y, m, brand, t, origin, wh, img, note = SALEMAP[sid]
    tname = TYPES[t][1]
    href = f"sale-{i}.html"
    hours = HOURS.get(sid, "On request")
    todo = f"<!-- TODO: sample hours ({hours}) – replace with the real hour-meter reading -->" if sid in HOURS else ""
    return f'''<article class="mc">
        <a class="mc-img" href="{href}">{img_tag(img + "-sm", f"Used {y} {m} {tname.lower()} for sale")}<span class="pill sale">For Sale</span><span class="pill export">Export available</span></a>
        <div class="mc-body">
          <div class="mc-yr">{y}</div>
          <h3><a href="{href}">{m}</a></h3>
          <div class="type">{tname} · Used</div>
          {todo}
          <div class="specs four"><div><strong>{wh:g} m</strong><span>Working ht.</span></div><div><strong>{hours}</strong><span>Hours</span></div><div><strong>{y}</strong><span>Year</span></div><div><strong>{origin}</strong><span>Origin</span></div></div>
          <div class="price"><b>Contact for price</b>UAE &amp; export enquiries</div>
          <div class="mc-btns">
            <a class="btn btn-navy btn-sm" href="#enquiry" data-want="buy">Enquire to Buy</a>
            <a class="btn btn-wa btn-icon" href="{wa_url(f"Hi, I'm interested in buying the used {y} {m}.")}" target="_blank" rel="noopener" aria-label="WhatsApp about the {y} {m}">{WA_SVG}</a>
          </div>
        </div>
      </article>'''


# height ranges as shown on the home page (reference v3)
HOME_RANGE = {"es": "7.8 – 15.7 m", "rt": "15.1 – 18.2 m", "eb": "13.5 – 20.4 m", "ab": "15.7 – 43.2 m", "tb": "15.7 – 28.2 m"}
HOME_NAV = [
    ("Rental", "rental.html", [(c["name"], c["file"], HOME_RANGE[k] + {"es": " · indoor", "rt": " · outdoor"}.get(k, ""))
                               for k, c in CATS.items()] + [("All rental machines →", "rental.html", "")]),
    ("Sales", "sales.html", [("Used Equipment", "sales-used.html", "Year, hours &amp; photos for every machine"),
                             ("New Equipment", "sales-new.html", ""), ("Sold Equipment", "sales-sold.html", "")]),
    ("Services", "services.html", [("AMC", "services-amc.html", "Annual maintenance contracts"),
                                   ("On-site Repairs", "services-on-site-repairs.html", "Breakdown repair at your site"),
                                   ("Workshop Services", "services-workshop.html", "Servicing &amp; overhaul in our workshop")]),
    ("About", "about.html", []),
    ("Blog", "blog.html", []),
    ("Contact", "contact.html", []),
]


def header_home():
    def dd(items):
        return "".join(f'<li><a href="{u}">{n}{f"<small>{s}</small>" if s else ""}</a></li>' for n, u, s in items)
    main = "".join(
        (f'<li class="has-dd"><a href="{u}">{n} {CARET}</a><ul class="dd">{dd(sub)}</ul></li>' if sub else f'<li><a href="{u}">{n}</a></li>')
        for n, u, sub in HOME_NAV)
    drawer = "".join(
        f'<li><a href="{u}">{n}</a>' + (f'<ul>{"".join(f"<li><a href=\"{su}\">{sn}</a></li>" for sn, su, _ in sub)}</ul>' if sub else "") + "</li>"
        for n, u, sub in HOME_NAV)
    return f'''<header class="site-hdr" id="hdr">
  <div class="wrap hdr">
    <a class="logo" href="index.html" aria-label="Cherry Pickers Equipment home"><img src="assets/img/logo.webp" alt="Cherry Pickers Equipment – The Right Pick for Every Height" width="1024" height="340"></a>
    <nav class="main" aria-label="Main">
      <ul>{main}</ul>
    </nav>
    <div class="hdr-cta">
      <a class="hdr-phone" href="{PHONE_LINK}" aria-label="Call {PHONE}">{icon("phone")}<span>{PHONE}</span></a>
      <a class="btn btn-wa btn-icon" href="{WA_LINK}" target="_blank" rel="noopener" aria-label="WhatsApp">{WA_SVG}</a>
      <a class="btn btn-red btn-sm" href="#enquiry" data-want="rent">Get a Quote</a>
      <button class="burger" id="burger" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="drawer"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
    </div>
  </div>
</header>
<div class="drawer" id="drawer" hidden>
  <div class="drawer-in" role="dialog" aria-modal="true" aria-label="Menu">
    <button class="x" id="drawerX" type="button" aria-label="Close menu">&times;</button>
    <nav aria-label="Mobile">
      <ul>{drawer}</ul>
    </nav>
    <a class="btn btn-red" href="#enquiry" data-want="rent">Get a Quote</a>
    <a class="btn btn-wa" href="{WA_LINK}" target="_blank" rel="noopener">{WA_SVG} WhatsApp Us</a>
  </div>
</div>'''


def footer_home():
    rent = "".join(f'<li><a href="{c["file"]}">{c["name"]}</a></li>' for c in CATS.values())
    social = "".join(f'\n        <a href="{u}" target="_blank" rel="noopener" aria-label="{n}">{icon(k)}</a>' for n, k, u in SOCIAL)
    return f'''<footer class="site-ftr">
  <div class="wrap ft">
    <div>
      <a class="ft-logo" href="index.html"><img src="assets/img/logo.webp" alt="Cherry Pickers Equipment" width="1024" height="340" loading="lazy"></a>
      <p>Boom lift and scissor lift rental across all seven UAE emirates, with maintenance and used equipment sales.</p>
      <div class="soc">{social}
      </div>
    </div>
    <div><h2 class="ft-h">Rental</h2><ul>{rent}</ul></div>
    <div><h2 class="ft-h">Sales &amp; Services</h2><ul><li><a href="sales-used.html">Used Equipment</a></li><li><a href="sales-new.html">New Equipment</a></li><li><a href="sales-sold.html">Sold Equipment</a></li><li><a href="services-amc.html">AMC</a></li><li><a href="services-on-site-repairs.html">On-site Repairs</a></li><li><a href="services-workshop.html">Workshop Services</a></li></ul></div>
    <div><h2 class="ft-h">Company</h2><ul><li><a href="about.html">About Us</a></li><li><a href="blog.html">Blog</a></li><li><a href="contact.html">Contact</a></li><li><a href="privacy-policy.html">Privacy Policy</a></li><li><a href="terms-and-conditions.html">Terms &amp; Conditions</a></li></ul></div>
    <div><h2 class="ft-h">Contact</h2><ul>
      <li>{ADDRESS}</li>
      <li><a href="{PHONE_LINK}">{PHONE}</a></li>
      <li>Breakdown 24/7: <a href="{BREAKDOWN_LINK}">{BREAKDOWN}</a></li>
      <li><a href="mailto:info@cherrypickersglobal.com">info@cherrypickersglobal.com</a></li>
      <li>Mon – Sat 9:00 – 19:00 · Sunday closed</li></ul></div>
  </div>
  <div class="wrap ft-bot">
    <span>© 2026 Cherry Pickers Equipment Rentals &amp; Maintenance LLC · Cherry Pickers Equipment LLC</span>
    <span>The Right Pick for Every Height</span>
  </div>
</footer>
<nav class="mbar" aria-label="Quick contact">
  <a href="{PHONE_LINK}">{icon("phone")}Call</a>
  <a class="wa" href="{WA_LINK}" target="_blank" rel="noopener">{WA_SVG}WhatsApp</a>
  <a class="q" href="#enquiry" data-want="rent">{icon("quote")}Get a Quote</a>
</nav>
<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Photo viewer"><button id="lbX" type="button" aria-label="Close">&times;</button><img id="lbImg" alt=""><p id="lbCap"></p></div>'''


def breadcrumbs(items):
    if not items:
        return ""
    lis = ['<li><a href="index.html">Home</a></li>']
    for i, (n, u) in enumerate(items):
        lis.append(f'<li aria-current="page">{n}</li>' if i == len(items) - 1 else f'<li><a href="{u}">{n}</a></li>')
    return f'<nav class="breadcrumbs wrap" aria-label="Breadcrumb"><ol>{"".join(lis)}</ol></nav>'


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
{robots}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{fonts}" rel="stylesheet">
<link rel="stylesheet" href="assets/css/{css}">
{head_extra}</head>
<body{body_class}>
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


# ------------------------------------------------------------------ shared enquiry section (above the footer on every page)
EMIRATES = "".join(f"<option>{e}</option>" for e in ("Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"))
ENQ = {
    "rental": dict(
        eyebrow="Get a quote", title="Need a Machine for Your Project?",
        text="Tell us the working height, the job and the site location. We'll suggest the right machine and send a quote.",
        tip="WhatsApp site photos and job details",
        fields='''<div class="field"><label>Machine needed</label><select><option>Not sure – advise me</option><option>Electric scissor lift</option><option>Rough terrain scissor lift</option><option>Electric boom lift</option><option>Articulated boom lift</option><option>Telescopic boom lift</option><option>Spider lift</option></select></div>
        <div class="field"><label>Emirate</label><select>''' + EMIRATES + '''</select></div>
        <div class="field full"><label>Job details</label><textarea placeholder="Working height, type of work, site location and dates"></textarea></div>''',
        button="Send enquiry"),
    "sales": dict(
        eyebrow="Buy a machine", title="Looking for a Specific Machine?",
        text="Tell us the model, year or working height you need. We source used boom lifts and scissor lifts worldwide.",
        tip="WhatsApp for photos and walk-around videos",
        fields='''<div class="field"><label>Machine or model</label><input placeholder="e.g. JLG 860SJ"></div>
        <div class="field"><label>Country</label><input placeholder="UAE or export country"></div>
        <div class="field full"><label>Message</label><textarea placeholder="Year range, working height, quantity or any questions"></textarea></div>''',
        button="Send enquiry"),
    "service": dict(
        eyebrow="Book a service", title="Tell Us About Your Machine",
        text="Send the brand, model and problem. Our workshop team will call you back.",
        tip="WhatsApp photos or videos of the fault",
        fields='''<div class="field"><label>Machine brand &amp; model</label><input placeholder="e.g. Genie GS-3246"></div>
        <div class="field"><label>Emirate</label><select>''' + EMIRATES + '''</select></div>
        <div class="field full"><label>Problem</label><textarea placeholder="What's wrong with the machine?"></textarea></div>''',
        button="Send request"),
}


def enquiry(kind="rental", title=None, text=None):
    e = ENQ[kind]
    return f'''<!-- ENQUIRY FORM (shared, above the footer) -->
<section class="section enquiry-section" id="enquiry-form">
  <div class="wrap enquiry-grid">
    <div>
      <span class="eyebrow">{e["eyebrow"]}</span>
      <h2>{title or e["title"]}</h2>
      <p class="muted">{text or e["text"]}</p>
      <ul class="tick-list">
        <li><a href="{PHONE_LINK}">{PHONE}</a></li>
        <li><a href="{WA_LINK}">{e["tip"]}</a></li>
        <li>Mon–Sat 9:00–19:00</li>
      </ul>
    </div>
    <form class="form-card" data-mock>
      <div class="form-grid">
        <div class="field"><label>Name <span class="req">*</span></label><input required></div>
        <div class="field"><label>Phone <span class="req">*</span></label><input required placeholder="+971"></div>
        {e["fields"]}
        <div class="full"><button class="btn btn--red btn--block" type="submit">{e["button"]}</button></div>
      </div>
      <div class="form-ok">Thanks – this is a mockup, nothing was sent.</div>
    </form>
  </div>
</section>'''


# ------------------------------------------------------------------ About sub-pages: shared "back to About" block
ABOUT_PAGES = [
    ("who-we-are", "Who we are", "about-who-we-are.html"),
    ("what-we-do", "What we do", "about-what-we-do.html"),
    ("who-we-work-with", "Who we work with", "about-who-we-work-with.html"),
    ("our-story", "Our story", "about-our-story.html"),
]


# Services sub-pages (Services menu: AMC / On-site Repairs / Workshop Services)
SERVICE_PAGES = [
    ("amc", "AMC – annual maintenance contracts", "services-amc.html"),
    ("on-site-repairs", "On-site repairs", "services-on-site-repairs.html"),
    ("workshop-services", "Workshop services", "services-workshop.html"),
    ("maintenance-repair", "Maintenance & repair overview", "maintenance-repair.html"),
]


def sub_nav(pages, current, back_href, back_label, title, label):
    """Back link to the parent page + links to the sibling pages (used at the end of About and Services sub-pages)."""
    chips = "".join(f'<a class="chip" href="{u}">{n}</a>' for k, n, u in pages if k != current)
    return f'''<!-- BACK TO PARENT + sibling pages -->
<section class="section section--alt section--tight">
  <div class="wrap">
    <a class="btn btn--navy" href="{back_href}">← {back_label}</a>
    <h2 style="font-size:1.3rem;margin:28px 0 12px">{title}</h2>
    <nav class="cat-chips" aria-label="{label}">{chips}</nav>
  </div>
</section>'''


def about_nav(current):
    """{{aboutnav:<key>}} – back link to the About page + links to the other About sub-pages."""
    return sub_nav(ABOUT_PAGES, current, "about.html", "Back to About Us", "More About Cherry Pickers Equipment", "About pages")


def services_nav(current):
    """{{servicesnav:<key>}} – back link to the Services page + links to the other service pages."""
    return sub_nav(SERVICE_PAGES, current, "services.html", "Back to Services", "More Services", "Service pages")


def render_tokens(html, kind="rental"):
    def _media(m):
        p = m.group(1).split("|")
        return media(p[0], p[1], p[2] if len(p) > 2 and p[2] else "ratio-4-3", len(p) > 3 and p[3] == "eager", p[4] if len(p) > 4 else "")
    html = re.sub(r"\{\{media:([^}]*)\}\}", _media, html)
    html = re.sub(r"\{\{heroimg:([^|}]*)\|([^}]*)\}\}", lambda m: hero_img(m.group(1), m.group(2)), html)
    html = re.sub(r"\{\{icon:(\w+)\}\}", lambda m: icon(m.group(1)), html)
    html = re.sub(r"\{\{rcard:(\w+)\}\}", lambda m: rental_card(m.group(1)), html)
    html = re.sub(r"\{\{scard:(\w+)\}\}", lambda m: sale_card(m.group(1)), html)
    # home page tokens
    html = re.sub(r"\{\{hrcard:(\w+)\}\}", lambda m: home_rcard(m.group(1)), html)
    html = re.sub(r"\{\{hscard:(\w+)\}\}", lambda m: home_scard(m.group(1)), html)
    html = html.replace("{{homefaq}}", home_faq_html())
    html = re.sub(r"\{\{aboutnav:([\w-]+)\}\}", lambda m: about_nav(m.group(1)), html)
    html = re.sub(r"\{\{servicesnav:([\w-]+)\}\}", lambda m: services_nav(m.group(1)), html)

    def _img(m):  # {{img:name|alt}} / {{img:name|alt|eager}} / {{img:name|alt||css style}}
        p = m.group(1).split("|")
        return img_tag(p[0], p[1], len(p) > 2 and p[2] == "eager", p[3] if len(p) > 3 else "")
    html = re.sub(r"\{\{img:([^}]*)\}\}", _img, html)
    html = re.sub(r"\{\{imgsize:([\w-]+)\}\}", lambda m: 'width="{}" height="{}"'.format(*_PIL.open(IMG / f"{m.group(1)}.webp").size), html)
    html = re.sub(r"\{\{wa:([^}]*)\}\}", lambda m: wa_url(m.group(1)), html)
    html = (html.replace("{{GOOGLE_REVIEWS_URL}}", GOOGLE_REVIEWS_URL).replace("{{GOOGLE_WRITE_REVIEW_URL}}", GOOGLE_WRITE_REVIEW_URL)
            .replace("{{BREAKDOWN}}", BREAKDOWN).replace("{{BREAKDOWN_LINK}}", BREAKDOWN_LINK).replace("{{tick}}", TICK))
    html = re.sub(r"\{\{form(?::([^}]*))?\}\}", lambda m: quick_form(m.group(1) or "Quick enquiry"), html)

    # {{cta}} / {{cta:title|text}} / {{cta:title|text|kind}} -> shared enquiry section
    def _c(m):
        p = (m.group(1) or "").split("|")
        k = p[2] if len(p) > 2 and p[2] else kind
        return enquiry(k, p[0] or None, p[1] if len(p) > 1 else None)
    html = re.sub(r"\{\{cta(?::([^}]*))?\}\}", _c, html)
    return (html.replace("{{PHONE}}", PHONE).replace("{{PHONE_LINK}}", PHONE_LINK)
            .replace("{{WA_LINK}}", WA_LINK).replace("{{ADDRESS}}", ADDRESS))


def rewrite_links(html, path):
    depth = path.count("/")
    root = "../" * depth

    def _href(m):
        name, rest = m.group(2), m.group(3) or ""
        if name not in LINKS:
            return m.group(0)
        return f'{m.group(1)}="{root}{LINKS[name]}index.html{rest}"'
    html = re.sub(r'(href)="([a-z0-9\-]+\.html)(#[^"]*)?"', _href, html)
    html = re.sub(r'((?:src|data-src|href))="assets/', lambda m: f'{m.group(1)}="{root}assets/', html)
    return html


# ------------------------------------------------------------------ page list
# out path, title, description, active nav, breadcrumbs, body (partial name or callable), noindex
PAGES = [
    ("index.html", "Boom Lift & Scissor Lift Rental in Dubai & UAE | Cherry Pickers Equipment",
     "Rent boom lifts and scissor lifts across all 7 UAE emirates – 30 models, 7.8 m to 43 m. Maintenance and used equipment sales too.", "home", [], "home"),
    ("about/index.html", "About Us – Access Equipment Rental Company in Dubai | Cherry Pickers Equipment",
     "Cherry Pickers Equipment rents scissor lifts and boom lifts across the UAE from Dubai Industrial City, with maintenance and used machine sales.", "about", [("About", "")], "about"),
    ("about/who-we-are/index.html", "Who We Are – Access Equipment Company in Dubai | Cherry Pickers Equipment",
     "Cherry Pickers Equipment is an access equipment company in Dubai Industrial City – rental, maintenance and used equipment sales from one team.",
     "about", [("About", "about.html"), ("Who We Are", "")], "about-who-we-are"),
    ("about/what-we-do/index.html", "What We Do – Rental, Maintenance & Equipment Sales | Cherry Pickers Equipment",
     "Boom lift and scissor lift rental, maintenance and repair, and used and new equipment sales across the UAE.",
     "about", [("About", "about.html"), ("What We Do", "")], "about-what-we-do"),
    ("about/who-we-work-with/index.html", "Who We Work With – Industries We Serve | Cherry Pickers Equipment",
     "Construction, facility management, malls and airports, warehousing, industrial, oil and gas, and events teams across the UAE use our machines.",
     "about", [("About", "about.html"), ("Who We Work With", "")], "about-who-we-work-with"),
    ("about/our-story/index.html", "Our Story, Vision & Mission | Cherry Pickers Equipment",
     "How Cherry Pickers Equipment grew from sourcing used access equipment into rental, sales, maintenance and safety support in the UAE.",
     "about", [("About", "about.html"), ("Our Story", "")], "about-our-story"),
    ("rental/index.html", "Scissor Lift & Boom Lift Rental in Dubai and the UAE | Cherry Pickers Equipment",
     f"Rent from {N_RENTAL} scissor lift and boom lift models, 7.8 m to 43 m working height. Daily to long-term hire across all 7 emirates, operators on request.", "rental", [("Rental", "")], page_rental_landing),
]
for c in CATS.values():
    PAGES.append((f"rental/{c['slug']}/index.html",
                  f"{c['one']} Rental in Dubai & UAE – {c['n']} Models | Cherry Pickers Equipment",
                  f"Rent {c['name'].lower()} in Dubai and across the UAE: {c['n']} models from {c['lo']} to {c['hi']} working height. Daily, weekly and monthly hire.",
                  "rental", [("Rental", "rental.html"), (c["name"], "")], (lambda c=c: page_rental_category(c))))
PAGES += [
    ("rental/electric-scissor-lifts/genie-gs-3246/index.html", "Genie GS-3246 Electric Scissor Lift for Rent in Dubai | Cherry Pickers Equipment",
     "Rent the Genie GS-3246 electric scissor lift in Dubai: 11.75 m working height, 318 kg capacity.", "rental",
     [("Rental", "rental.html"), ("Electric Scissor Lifts", CATS["es"]["file"]), ("Genie GS-3246", "")], "rental-detail"),
    ("sales/index.html", "Used Boom Lifts & Scissor Lifts for Sale – UAE & Export | Cherry Pickers Equipment",
     f"Buy used JLG and Genie boom lifts and scissor lifts. {len(SALE)} machines available, {N_SOLD} sold and exported. Contact for price.", "sales", [("Sales", "")], page_sales_landing),
    ("sales/new/index.html", "New Access Equipment for Sale in UAE | Cherry Pickers Equipment",
     "New boom lifts and scissor lifts for sale in the UAE. Tell us the machine you need for price and delivery time.", "sales",
     [("Sales", "sales.html"), ("New Equipment", "")], page_sales_new),
    ("sales/used/index.html", "Used Access Equipment for Sale in UAE | Cherry Pickers Equipment",
     f"{len(SALE)} used boom lifts for sale with year, origin and photos. Filter by type, brand, year and working height.", "sales",
     [("Sales", "sales.html"), ("Used Equipment", "")], page_sales_used),
    ("sales/sold/index.html", f"Sold Access Equipment – {N_SOLD} Sales Records | Cherry Pickers Equipment",
     f"Records of {N_SOLD} used boom lifts and scissor lifts sold and exported by Cherry Pickers Equipment, by model, year and destination.", "sales",
     [("Sales", "sales.html"), ("Sold Equipment", "")], page_sales_sold),
    ("sales/used/2010-jlg-600aj/index.html", "Used 2010 JLG 600AJ Articulated Boom Lift for Sale | Cherry Pickers Equipment",
     "Used 2010 JLG 600AJ articulated boom lift for sale: 20.5 m working height, Australian origin. Contact for price.", "sales",
     [("Sales", "sales.html"), ("Used Equipment", "sales-used.html"), ("2010 JLG 600AJ", "")], "sale-detail"),
    (SOLD_SAMPLE_PATH, f"Sold: {SOLD_SAMPLE['year']} {SOLD_SAMPLE['model']} {TYPES[SOLD_SAMPLE['t']][1]} | Cherry Pickers Equipment",
     f"{SOLD_SAMPLE['year']} {SOLD_SAMPLE['model']} {TYPES[SOLD_SAMPLE['t']][1].lower()} from {SOLD_SAMPLE['origin']}, sold {fmt_date(SOLD_SAMPLE['date'])}"
     f"{' to ' + SOLD_SAMPLE['to'] if SOLD_SAMPLE['to'] else ''}. Looking for one like it? We source used JLG and Genie machines.", "sales",
     [("Sales", "sales.html"), ("Sold Equipment", "sales-sold.html"), (f"{SOLD_SAMPLE['year']} {SOLD_SAMPLE['model']}", "")],
     (lambda: page_sold_detail(SOLD_SAMPLE))),
    ("services/index.html", "Access Equipment Services in UAE | Cherry Pickers Equipment",
     "Equipment rental, maintenance and repair, and used machine sales across the UAE.", "services", [("Services", "")], "services"),
    ("services/maintenance-repair/index.html", "MEWP Maintenance & Repair in Dubai & UAE | Cherry Pickers Equipment",
     "Maintenance contracts (AMC), servicing and breakdown repair for boom lifts and scissor lifts.", "services",
     [("Services", "services.html"), ("Maintenance & Repair", "")], "maintenance"),
    ("services/amc/index.html", "AMC – Annual Maintenance Contracts for Boom Lifts & Scissor Lifts | Cherry Pickers Equipment",
     "Annual maintenance contracts (AMC) for boom lifts and scissor lifts: planned service visits on a fixed schedule, across all seven UAE emirates.",
     "services", [("Services", "services.html"), ("AMC", "")], "services-amc"),
    ("services/on-site-repairs/index.html", "On-site Boom Lift & Scissor Lift Repairs in the UAE | Cherry Pickers Equipment",
     "Breakdown repair at your site for boom lifts and scissor lifts – hydraulic, electrical and drive faults. 24/7 breakdown line +971 56 801 9344.",
     "services", [("Services", "services.html"), ("On-site Repairs", "")], "services-on-site-repairs"),
    ("services/workshop-services/index.html", "Workshop Servicing & Overhaul for Boom Lifts & Scissor Lifts | Cherry Pickers Equipment",
     "Servicing, repair and overhaul of boom lifts and scissor lifts in our workshop in Dubai Industrial City – for machines you own.",
     "services", [("Services", "services.html"), ("Workshop Services", "")], "services-workshop"),
    ("blog/index.html", "Blog – Access Equipment Guides & Tips | Cherry Pickers Equipment",
     "Guides on choosing, renting and operating boom lifts and scissor lifts in the UAE.", "blog", [("Blog", "")], "blog"),
    ("blog/boom-lift-vs-scissor-lift/index.html", "Boom Lift vs Scissor Lift: How to Choose | Cherry Pickers Equipment",
     "How to choose between a boom lift and a scissor lift for your UAE project.", "blog",
     [("Blog", "blog.html"), ("Boom Lift vs Scissor Lift", "")], "blog-detail"),
    ("contact/index.html", "Contact Us | Cherry Pickers Equipment, Dubai Industrial City",
     "Call, WhatsApp or send an enquiry for access equipment rental, maintenance or sales.", "contact", [("Contact", "")], "contact"),
    ("privacy-policy/index.html", "Privacy Policy | Cherry Pickers Equipment",
     "How Cherry Pickers Equipment collects and uses personal information.", "", [("Privacy Policy", "")], "legal"),
    ("terms-and-conditions/index.html", "Terms & Conditions | Cherry Pickers Equipment",
     "Rental, maintenance and sales terms of Cherry Pickers Equipment.", "", [("Terms & Conditions", "")], "terms"),
]


# ------------------------------------------------------------------ WhatsApp pre-filled messages
# Every wa.me link on a page gets the message for that page (header icon, buttons, mobile bar, footer).
WA_HI = "Hi Cherry Pickers Equipment,"
WA_RENT = "\nWorking height:\nSite location:\nDates:"
WA_DEFAULT = f"{WA_HI} I'd like more information about your access equipment."
WA_MSG = {
    "rental/index.html": f"{WA_HI} I'd like a rental quote.\nMachine type:" + WA_RENT,
    "rental/electric-scissor-lifts/genie-gs-3246/index.html": f"{WA_HI} I'd like a quote to rent the Genie GS-3246 electric scissor lift.\nSite location:\nDates:",
    "sales/index.html": f"{WA_HI} I'm interested in buying a used machine.\nModel:\nWorking height:\nCountry:",
    "sales/new/index.html": f"{WA_HI} I'm interested in buying a new machine.\nModel:\nCountry:",
    "sales/used/index.html": f"{WA_HI} I'm interested in one of your used machines for sale.\nModel:\nCountry:",
    "sales/sold/index.html": f"{WA_HI} I'm looking for a machine like the ones you have sold.\nModel:\nYear range:\nCountry:",
    "sales/used/2010-jlg-600aj/index.html": f"{WA_HI} I'm interested in the used 2010 JLG 600AJ articulated boom lift. Please send the price and more photos.\n{SITE}sales/used/2010-jlg-600aj/",
    "services/index.html": f"{WA_HI} I'd like to know more about your services.",
    "services/maintenance-repair/index.html": f"{WA_HI} I need service or repair for a machine.\nBrand & model:\nProblem:\nLocation:",
    "contact/index.html": f"{WA_HI} I have an enquiry.",
    "services/amc/index.html": f"{WA_HI} I'd like a quote for an annual maintenance contract (AMC).\nMachines (brand & model):\nNumber of machines:\nLocation:",
    "services/on-site-repairs/index.html": f"{WA_HI} I have a machine breakdown and need an on-site repair.\nBrand & model:\nProblem:\nLocation:",
    "services/workshop-services/index.html": f"{WA_HI} I'd like to book a workshop service.\nBrand & model:\nWork needed:",
}
WA_MSG[SOLD_SAMPLE_PATH] = (f"{WA_HI} I'm looking for a machine like the {SOLD_SAMPLE['year']} {SOLD_SAMPLE['model']} you sold.\n"
                            f"Year range:\nCountry:\n{SITE}{SOLD_SAMPLE_PATH.replace('index.html', '')}")
for _c in CATS.values():
    _m = _c['one'].lower()
    WA_MSG[f"rental/{_c['slug']}/index.html"] = f"{WA_HI} I'd like a quote to rent {'an' if _m[0] in 'aeiou' else 'a'} {_m}." + WA_RENT


def wa_prefill(html, path):
    msg = quote(WA_MSG.get(path, WA_DEFAULT), safe="")
    return html.replace(f'href="{WA_LINK}"', f'href="{WA_LINK}?text={msg}"')


def build():
    # remove old flat pages from the previous mockup version
    for old in OUT.glob("*.html"):
        if old.name != "index.html":
            old.unlink()
    # /sales/available/ was renamed to /sales/used/
    shutil.rmtree(OUT / "sales" / "available", ignore_errors=True)
    built = []
    for path, title, desc, active, crumbs, body in PAGES:
        raw = body() if callable(body) else (SRC / "pages" / f"{body}.html").read_text(encoding="utf-8")
        robots = '<meta name="robots" content="noindex, follow">\n' if path == "sales/new/index.html" and not NEW else ""
        kind = {"sales": "sales", "services": "service"}.get(active, "rental")
        body_html, crumbs_html = render_tokens(raw, kind), breadcrumbs(crumbs)
        home = path == "index.html"
        # every page ends with the shared enquiry form, except Contact (own full form) and Home (own #enquiry section)
        if 'class="section enquiry-section"' not in body_html and 'id="enquiry"' not in body_html and path != "contact/index.html":
            body_html = body_html.rstrip() + "\n\n" + enquiry(kind) + "\n"
        # breadcrumbs sit inside the photo hero when the page has one; otherwise above the content
        hero = re.search(r'<section class="r-hero[^"]*">\n', body_html)
        if hero and crumbs_html:
            body_html = body_html[:hero.end()] + "  " + crumbs_html + "\n" + body_html[hero.end():]
            crumbs_html = ""
        html = PAGE.format(title=title.replace("&", "&amp;"), desc=desc.replace("&", "&amp;"),
                           canonical=SITE + path.replace("index.html", ""), robots=robots,
                           fonts=HOME_FONTS if home else SITE_FONTS,
                           css="home.css" if home else "style.css",
                           head_extra=home_faq_jsonld() if home else "",
                           body_class=' class="home"' if home else "",
                           header=header_home() if home else header(active), crumbs=crumbs_html, body=body_html,
                           footer=footer_home() if home else footer())
        html = wa_prefill(rewrite_links(html, path), path)
        out = OUT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        built.append(path)
    print(f"Built {len(built)} pages")


if __name__ == "__main__":
    build()
