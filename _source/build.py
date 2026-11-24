"""Cherry Pickers Equipment – HTML mockup builder (v3: /rental/{category}/ and /sales/ structure).

Pages mirror the final WordPress URLs as folders with index.html:
  /rental/                       rental landing (SEO content + image category tiles)
  /rental/all-machines/          filterable list of the whole rental fleet (target of the home page machine finder)
  /rental/{category}/            category listing with category-specific filters
  /sales/                        sales landing (SEO content + image category tiles)
  /sales/new/                    new equipment (empty-state + noindex while NEW is empty)
  /sales/used/                   filterable used stock listing
  /sales/sold/                   filterable sold records (212, from the live Sold page)
Partials in ./pages use flat names (e.g. href="contact.html"); rewrite_links() maps them to folder URLs.
"""
import json
import re
from html import escape as html_escape
from urllib.parse import quote
import shutil
from collections import Counter, OrderedDict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from PIL import Image as _PIL

from legacy import icon, WA_SVG, PHONE, PHONE_LINK, WA_LINK, ADDRESS, quick_form
from quote import quote_attrs, quote_inline, quote_modal, CATEGORIES as QUOTE_CATEGORIES

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
    "rental-all.html": "rental/all-machines/",
    "rental-category.html": "rental/scissor-lifts/slab-electric-scissor-lifts/",
    "rental-detail.html": "rental/genie-gs-3246/",
    "sales.html": "sales/",
    "equipment-for-sale.html": "sales/",
    "sales-new.html": "sales/new/",
    "sales-used.html": "sales/used/",
    "sales-available.html": "sales/used/",  # alias for old partial links
    "sales-sold.html": "sales/sold/",
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

# ------------------------------------------------------------------ machine data (single source: data/machines.json)
# Shaped like WordPress posts of a 'machine' post type: taxonomies (machine_type, machine_brand, listing_status)
# + ACF fields (model, year, working_height, ...). See WORDPRESS-MAP.md. Nothing else in this file holds machine data.
MACHINES = json.loads((SRC / "data" / "machines.json").read_text(encoding="utf-8"))["machines"]


def tax(it, key):
    return it["taxonomies"][key]


def acf(it, key):
    """ACF field value (None when not recorded)."""
    return it["acf"].get(key)


def by_status(status):
    return [it for it in MACHINES if tax(it, "listing_status") == status]


RENTAL_ITEMS = by_status("rental")
USED = by_status("used")
NEW = by_status("new")      # new equipment for sale; none yet -> /sales/new/ shows an enquiry panel and is noindexed
SOLD = by_status("sold")
N_SOLD = len(SOLD)
# lookup for {{card:status:slug}} tokens in the hand-written partials
BY_KEY = {f"{tax(it, 'listing_status')}:{it['slug']}": it for it in MACHINES}
# taxonomy term names (WordPress: the machine_brand term name)
BRAND_NAMES = {"jlg": "JLG", "genie": "Genie", "dingli": "Dingli", "snorkel": "Snorkel"}
CONTAIN = {"r-gs5390", "r-z4525j", "r-z4525ic", "r-800aj", "r-gs1932", "r-510aj", "r-s80x", "r-z6034"}

def r1(x):
    """One decimal, rounded half up (43.15 -> 43.2, 18.15 -> 18.2), as in the site copy; float() keeps :g formatting working."""
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


# ------------------------------------------------------------------ rental categories
CATS = OrderedDict()
CATS["se"] = dict(
    slug="slab-electric-scissor-lifts", name="Slab Electric Scissor Lifts", one="Slab Electric Scissor Lift", menu="Slab Electric",
    img="cat-electric-scissor",
    short="Compact, quiet electric scissors for smooth indoor floors and standard doorways.",
    h1="Slab Electric Scissor Lift Rental in Dubai & UAE",
    intro="Slab electric scissor lifts are compact, quiet, zero-emission work platforms that lift workers and tools straight up on smooth, level floors. We rent {n} slab electric models from {lo} to {hi} working height for indoor fit-out, warehouses, malls and maintenance work, by the day, week or month, across all seven emirates.",
    hb=[(0, 10, "Up to 10 m"), (10, 99, "10 m and above")],
    second=("cap", "Platform capacity", [(0, 300, "Up to 300 kg"), (300, 400, "300 – 399 kg"), (400, 9999, "400 kg and above")]),
    uses=["Ceiling, lighting and MEP installation", "Warehouse racking and maintenance", "Mall, airport and hotel interior work",
          "Painting, signage and fit-out", "Facility maintenance on smooth, level floors"],
    choose=[("Working height", "Working height is platform height plus about 2 m (a person's reach). Pick a machine a little above your highest work point."),
            ("Width and doors", "Check door and corridor widths before you book – our narrowest slab scissors pass through standard doors."),
            ("Floor", "Slab scissor lifts need smooth, firm, level floors. For outdoor or uneven ground, choose a rough terrain electric or diesel 4x4 scissor lift."),
            ("Weight on the platform", "Add up people, tools and materials. Our slab electric scissors carry 227 kg to 454 kg.")],
    faq=[("What is the difference between working height and platform height?", "Platform height is how high the platform floor goes. Working height adds about 2 m for the person's reach. A Genie GS-3246 has a 9.78 m platform height and an 11.75 m working height."),
         ("Can slab electric scissor lifts be used outdoors?", "Only on firm, level, paved ground in low wind. For uneven ground, choose a rough terrain electric or diesel 4x4 scissor lift."),
         ("Can I rent a slab electric scissor lift for one day?", "Yes. We rent by the day, week or month, and long-term."),
         ("Do you supply an operator?", "Yes, on request. Tell us when you book.")])
CATS["re"] = dict(
    slug="rough-terrain-electric-scissor-lifts", name="Rough Terrain Electric Scissor Lifts", one="Rough Terrain Electric Scissor Lift",
    menu="Rough Terrain Electric", img="r-m4069le",
    short="Heavy-duty battery scissors for firm outdoor ground – zero emissions, low noise.",
    h1="Rough Terrain Electric Scissor Lift Rental in Dubai & UAE",
    intro="Rough terrain electric scissor lifts are heavy-duty battery work platforms with zero emissions, built for firm outdoor ground as well as large indoor sites. We rent {n} rough terrain electric models from {lo} to {hi} working height across all seven emirates, by the day, week or month.",
    hb=[(0, 14, "Up to 14 m"), (14, 99, "14 m and above")],
    second=("cap", "Platform capacity", [(0, 300, "Up to 300 kg"), (300, 9999, "300 kg and above")]),
    uses=["Outdoor fit-out and facade work on firm ground", "Sites with noise or exhaust limits", "Large warehouses, factories and logistics yards",
          "Car parks, podiums and paved site areas", "Mixed indoor and outdoor work on one site"],
    choose=[("Ground conditions", "These machines work on firm, uneven ground outdoors. [Add: gradeability and ground clearance for the Dingli 1412HD / 1612HD and JLG M4069LE.]"),
            ("Working height", "Our rough terrain electric scissors reach 13.8 m to 15.7 m."),
            ("Weight on the platform", "They carry 250 kg to 362 kg – add up people, tools and materials together."),
            ("Shift length", "[Add: typical battery runtime and charging needs for your machines.]")],
    faq=[("What is the difference between a rough terrain electric and a diesel 4x4 scissor lift?", "Both work on outdoor ground. Rough terrain electric models run on batteries with zero emissions and little noise. Diesel 4x4 models carry heavier loads (up to 680 kg) and reach higher, up to 18.2 m."),
         ("Can rough terrain electric scissor lifts be used indoors?", "Yes. They are electric, so they suit large indoor sites too – check that the floor can take the machine's weight (3.4 – 4.9 tonnes)."),
         ("How long does the battery last?", "[Your answer – typical hours per charge for your machines.]"),
         ("Do you supply an operator?", "Yes, on request. Tell us when you book.")])
CATS["dz"] = dict(
    slug="diesel-4x4-scissor-lifts", name="Diesel 4x4 Scissor Lifts", one="Diesel 4x4 Scissor Lift", menu="Diesel 4x4", img="cat-rt-scissor",
    short="Diesel four-wheel-drive platforms with big decks for outdoor sites and rough ground.",
    h1="Diesel 4x4 Scissor Lift Rental in Dubai & UAE",
    intro="Diesel 4x4 scissor lifts are rough terrain work platforms with four-wheel drive and large decks, built for outdoor sites and uneven ground. We rent {n} diesel 4x4 models from {lo} to {hi} working height, each carrying up to 680 kg, across all seven emirates.",
    hb=[(0, 16, "Up to 16 m"), (16, 99, "16 m and above")],
    second=("cap", "Platform capacity", [(600, 9999, "600 kg and above")]),
    uses=["Construction sites and building shells", "Cladding, facade and glazing work", "Steel and structural installation",
          "Outdoor events and exhibitions", "Infrastructure and industrial yards"],
    choose=[("Ground conditions", "Diesel 4x4 models handle compacted soil, gravel and slopes – check the site gradient before booking."),
            ("Deck size and load", "Large decks carry crews, panels and tools together – up to 680 kg on our machines."),
            ("Working height", "Our diesel 4x4 scissors reach 15.1 m to 18.2 m."),
            ("Access and transport", "These machines are large and heavy (5.9 – 7.5 tonnes) – confirm site access for delivery.")],
    faq=[("Can a diesel 4x4 scissor lift be used indoors?", "They run on diesel, so they are not suited to enclosed spaces without proper ventilation. Indoors, use a slab electric or rough terrain electric scissor lift."),
         ("How much weight can a diesel 4x4 scissor lift carry?", "Our Genie GS-4390 RT and GS-5390 RT carry up to 680 kg – people, tools and materials together."),
         ("What is the difference between a diesel 4x4 and an electric scissor lift?", "Diesel 4x4 models are built for rough outdoor ground and the heaviest loads. Slab electric models are quiet and compact for smooth indoor floors; rough terrain electric models handle firm outdoor ground with zero emissions.")])
CATS["eb"] = dict(
    slug="electric-boom-lifts", menu="Electric", name="Electric Boom Lifts", one="Electric Boom Lift", img="cat-electric-boom",
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
    slug="articulated-boom-lifts", menu="Articulated", name="Articulated Boom Lifts", one="Articulated Boom Lift", img="cat-articulated",
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
    slug="telescopic-boom-lifts", menu="Telescopic", name="Telescopic Boom Lifts", one="Telescopic Boom Lift", img="cat-telescopic",
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

# Sub-category order (menu, filters, height table): boom types first, then scissor types – as in the client's brief.
CATS = OrderedDict((k, CATS[k]) for k in ("tb", "ab", "eb", "se", "re", "dz"))

# ------------------------------------------------------------------ rental MAIN categories (parent machine_type terms)
# WordPress: hierarchical machine_type taxonomy. A parent term's page (taxonomy-machine_type.php) shows content + one
# card per child term (template-parts/category-card.php). Spider has no child terms yet: term meta status=coming-soon.
GROUPS = OrderedDict()
GROUPS["boom"] = dict(
    slug="boom-lifts", name="Boom Lifts", one="Boom Lift", img="cat-articulated", subs=["tb", "ab", "eb"],
    cmp=("outreach", "Outreach"),
    short="Telescopic, articulated and electric booms that reach up and out – up to 43 m.",
    h1="Boom Lift Rental in Dubai & UAE",
    intro="Boom lifts raise a work platform up and out on an arm, so you can reach over obstacles and work away from the base. We rent {n} boom lift models in three types – telescopic, articulated and electric – from {lo} to {hi} working height, by the day, week or month, across all seven emirates.",
    title="Boom Lift Rental in Dubai & UAE – {n} Models | Cherry Pickers Equipment",
    desc="Rent telescopic, articulated and electric boom lifts in Dubai and across the UAE: {n} models, {lo} to {hi} working height. Daily to long-term hire.",
    when={"tb": ["You need the <strong>longest straight reach</strong> from one position", "Nothing is in the way between the machine and the work", "Facades, steel erection, bridges and large structures"],
          "ab": ["Obstacles are in the way – the arm bends <strong>up and over</strong>", "You need tight spots behind or above other equipment", "Piping, MEP, plants and roof work"],
          "eb": ["You work <strong>indoors</strong> or in noise-sensitive areas", "No exhaust is allowed – malls, airports, atriums", "Night work and occupied buildings"]},
    uses=["Facades, glazing and cladding", "Steel structures and roof work", "Piping and MEP work over obstacles",
          "Atriums, malls and airport terminals", "Industrial plants, tanks and yards"],
    faq=[("What is a boom lift?", "A boom lift (also called a cherry picker) is a work platform on a telescopic or jointed arm, mounted on a wheeled base. It reaches up and out, so you can work away from the machine or over obstacles."),
         ("Telescopic, articulated or electric – which boom lift do I need?", "Telescopic for the longest straight reach, articulated when you need to go up and over obstacles, and electric for indoor or noise-sensitive work with no exhaust."),
         ("What is the tallest boom lift you rent?", "The Genie Z-135/70 articulated boom, with a 43.15 m working height and 21.25 m outreach."),
         ("Do you supply an operator?", "Yes, on request. Tell us when you book.")])
GROUPS["scissor"] = dict(
    slug="scissor-lifts", name="Scissor Lifts", one="Scissor Lift", img="cat-electric-scissor", subs=["se", "re", "dz"],
    cmp=("platform_height", "Platform height"),
    short="Slab electric, rough terrain electric and diesel 4x4 platforms that go straight up.",
    h1="Scissor Lift Rental in Dubai & UAE",
    intro="Scissor lifts raise a large work platform straight up, carrying several people with tools and materials. We rent {n} scissor lift models in three types – slab electric, rough terrain electric and diesel 4x4 – from {lo} to {hi} working height, by the day, week or month, across all seven emirates.",
    title="Scissor Lift Rental in Dubai & UAE – {n} Models | Cherry Pickers Equipment",
    desc="Rent slab electric, rough terrain electric and diesel 4x4 scissor lifts in Dubai and across the UAE: {n} models, {lo} to {hi} working height.",
    when={"se": ["<strong>Smooth, level floors</strong> indoors", "You need to pass standard doors, lifts and corridors", "Fit-out, ceilings, lighting and warehouse work"],
          "re": ["<strong>Firm outdoor ground</strong> with zero emissions", "Sites with noise or exhaust limits", "Mixed indoor and outdoor work on one site"],
          "dz": ["<strong>Rough outdoor ground</strong>, gravel or slopes", "Heavy loads – up to 680 kg on a large deck", "Construction sites, cladding and steel work"]},
    uses=["Ceiling, lighting and MEP installation", "Warehouse racking and maintenance", "Cladding, facade and glazing work",
          "Construction sites and building shells", "Events, exhibitions and fit-out"],
    faq=[("What is a scissor lift?", "A scissor lift is a work platform raised straight up by criss-cross supports. It has a larger deck than a boom lift and carries several people with tools and materials."),
         ("Which scissor lift do I need?", "Slab electric for smooth indoor floors, rough terrain electric for firm outdoor ground with zero emissions, and diesel 4x4 for rough ground and the heaviest loads."),
         ("What is the difference between working height and platform height?", "Platform height is how high the platform floor goes. Working height adds about 2 m for the person's reach."),
         ("Should I rent a scissor lift or a boom lift?", "Choose a scissor lift to go straight up with a large platform. Choose a boom lift when you need to reach up and out, or over obstacles.")])
GROUPS["spider"] = dict(
    slug="spider-lifts", name="Spider Lifts", one="Spider Lift", img="cat-spider", subs=[], soon=True,
    lo="17 m", hi="36 m", range="17 – 36 m",
    short="Compact tracked booms for tight access, slopes and delicate floors – 17 to 36 m, coming soon.",
    h1="Spider Lift Rental in Dubai & UAE",
    intro="Spider lifts are compact booms on rubber tracks with outriggers. They fit through narrow access, are light on delicate floors and level themselves on slopes, steps or soft ground. Spider lifts from {lo} to {hi} working height are joining our rental fleet soon – register your interest and we'll contact you first.",
    title="Spider Lift Rental in Dubai & UAE – Coming Soon | Cherry Pickers Equipment",
    desc="Tracked spider lifts from {lo} to {hi} working height are joining our UAE rental fleet. Register interest for tight-access, delicate-floor and sloped sites.",
    when={"spider": ["Access is <strong>tight</strong> – narrow doors, gates or corridors",
                     "Floors are delicate or the ground is soft (light weight, non-marking tracks)",
                     "You set up on slopes, steps or uneven ground (outriggers level the machine)",
                     "Atriums, lobbies, glazing and tree work, indoors or outdoors"]},
    uses=["Atriums, lobbies and shopping malls", "Glazing and facade work behind landscaping", "Halls, places of worship and heritage buildings",
          "Tree work and outdoor maintenance on soft ground", "Sites reached through gates, doors or narrow paths"],
    faq=[("What is a spider lift and when do I need one?", "A spider lift is a compact boom on rubber tracks with outriggers. It fits through narrow access, is light on delicate floors and levels itself on slopes, stairs or soft ground. Choose one when access is tight or the floor cannot take a standard boom."),
         ("When will spider lifts be available?", "Spider lifts from 17 m to 36 m working height are joining our fleet soon. Register your interest and we'll contact you as soon as they arrive."),
         ("What can I use until then?", "For indoor work on smooth floors, an electric boom lift or slab electric scissor lift often does the job. Tell us the site and we'll suggest a machine from our current fleet.")])

for gk, g in GROUPS.items():
    g["key"] = gk
    g["file"] = f"rental-{g['slug']}.html"
    LINKS[g["file"]] = f"rental/{g['slug']}/"
    for k in g["subs"]:
        CATS[k]["parent"] = gk

for k, c in CATS.items():
    ms = [it for it in RENTAL_ITEMS if tax(it, "machine_type") == c["slug"]]
    whs = [acf(it, "working_height") for it in ms]
    c["key"] = k
    c["group"] = GROUPS[c["parent"]]
    c["models"] = ms
    c["n"] = len(ms)
    c["lo"] = f"{min(whs):g} m"
    c["hi"] = f"{max(whs):g} m"
    c["range"] = f"{r1(min(whs))} – {r1(max(whs))} m"
    c["file"] = f"rental-{c['slug']}.html"
    c.setdefault("search", True)   # listing search on this category page (False = no search markup)
    LINKS[c["file"]] = f"rental/{c['group']['slug']}/{c['slug']}/"
N_RENTAL = len(RENTAL_ITEMS)

for g in GROUPS.values():
    g["cats"] = [CATS[k] for k in g["subs"]]
    g["models"] = [it for c in g["cats"] for it in c["models"]]
    g["n"] = len(g["models"])
    if g["models"]:
        whs = [acf(it, "working_height") for it in g["models"]]
        g["lo"], g["hi"] = f"{min(whs):g} m", f"{max(whs):g} m"
        g["range"] = f"{r1(min(whs))} – {r1(max(whs))} m"

# Machine pages are flat (/rental/{slug}/), so a machine slug must never equal a category URL segment.
_clash = {it["slug"] for it in RENTAL_ITEMS} & ({g["slug"] for g in GROUPS.values()} | {"all-machines"})
assert not _clash, f"rental machine slug clashes with a category URL: {_clash}"

# Old flat rental category URLs (before the main/sub split) -> where they 301 now. Feeds _source/redirects.csv.
# electric-scissor-lifts was split into two sub-categories, so it goes to the Scissor Lifts main page.
OLD_RENTAL_CATS = {"electric-scissor-lifts": "rental/scissor-lifts/",
                   "rough-terrain-scissor-lifts": "rental/scissor-lifts/diesel-4x4-scissor-lifts/",
                   "electric-boom-lifts": "rental/boom-lifts/electric-boom-lifts/",
                   "articulated-boom-lifts": "rental/boom-lifts/articulated-boom-lifts/",
                   "telescopic-boom-lifts": "rental/boom-lifts/telescopic-boom-lifts/"}
# new machine_type -> the old one (old machine URLs were /rental/{old machine_type}/{slug}/)
OLD_TYPE = {"slab-electric-scissor-lifts": "electric-scissor-lifts", "rough-terrain-electric-scissor-lifts": "electric-scissor-lifts",
            "diesel-4x4-scissor-lifts": "rough-terrain-scissor-lifts"}

# machine_type term -> (sales group, label shown on sales/sold cards). Scissor types share one sales label.
TYPES = {"telescopic-boom-lifts": ("telescopic", "Telescopic Boom Lift"), "articulated-boom-lifts": ("articulated", "Articulated Boom Lift"),
         "slab-electric-scissor-lifts": ("scissor", "Scissor Lift"), "rough-terrain-electric-scissor-lifts": ("scissor", "Scissor Lift"),
         "diesel-4x4-scissor-lifts": ("scissor", "Scissor Lift"),
         "electric-boom-lifts": ("electric-boom", "Electric Boom Lift")}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

# Model specs we already hold: rental fleet (full specs) and used stock (working height only) – used on sold detail pages
MODEL_RENT = {acf(it, "model"): it for it in RENTAL_ITEMS}
MODEL_WH = {acf(it, "model"): acf(it, "working_height") for it in USED}
MODEL_WH.update({acf(it, "model"): acf(it, "working_height") for it in RENTAL_ITEMS})


def fmt_date(d):
    """sold_date 'YYYY-MM' ('YYYY-00' = month unknown) -> 'Nov 2025' / '2025'."""
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
# machine-<id>.html -> the machine's permalink (WordPress: get_permalink()):
#   rental        -> rental/<slug>/                               e.g. rental/genie-s-65/ (category only in the breadcrumbs)
#   used/new/sold -> sales/<year>-<brand>-<model>-<stock id>/     e.g. sales/2010-jlg-600aj-cp112/
# Sales URLs carry no status, so a machine keeps its URL when it sells (used -> sold): no redirect needed.
# The stock ID keeps every sales URL unique (same model + year sold several times).
def stock_id(it):
    """ACF stock_no as a URL segment. Not recorded yet for any machine -> mockup placeholder 'cp' + post ID."""
    return slug(acf(it, "stock_no") or f"cp{it['id']}")


def sales_slug(it):
    """{year}-{brand}-{model}-{stock id}, e.g. 2010-jlg-600aj-cp112 (WordPress: post_name set on save)."""
    brand = tax(it, "machine_brand")
    model = slug(acf(it, "model"))
    model = model[len(brand) + 1:] if model.startswith(brand + "-") else model
    return f"{acf(it, 'year')}-{brand}-{model}-{stock_id(it)}"


def machine_path(it):
    if tax(it, "listing_status") == "rental":
        return f"rental/{it['slug']}/"
    return f"sales/{sales_slug(it)}/"


def machine_href(it):
    return f"machine-{it['id']}.html"


# The mockup renders each detail template ONCE, for a sample machine. WordPress renders the same template for every
# machine at its own permalink (post_name in the DB). In the mockup, every card's Details link opens its template's sample.
DETAIL_SAMPLE = {
    "rental": BY_KEY["rental:genie-gs-3246"],
    "used": BY_KEY["used:2010-jlg-600aj"],
    "sold": next(it for it in SOLD if acf(it, "model") == "JLG 860SJ" and acf(it, "year") == 2015
                 and acf(it, "sold_to") and acf(it, "sold_date")),
}
for _it in MACHINES:
    LINKS[machine_href(_it)] = machine_path(DETAIL_SAMPLE.get(tax(_it, "listing_status"), DETAIL_SAMPLE["used"]))
LINKS["sale-detail.html"] = machine_path(BY_KEY["used:2010-jlg-600aj"])
# sales machine URLs share /sales/ with the listing pages; a year-first slug can never be one of them
_sales = [machine_path(it) for it in MACHINES if tax(it, "listing_status") != "rental"]
assert len(set(_sales)) == len(_sales), "two sales machines share a URL – check stock_no"
assert not {p.split("/")[1] for p in _sales} & {"new", "used", "sold"}, "sales machine URL clashes with a listing page"
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


STATUS = {"available": '<span class="badge badge--ok">Available</span>',
          "on-hire": '<span class="badge badge--busy">On hire – ask for date</span>'}
WA_NUMBER = WA_LINK.rsplit("/", 1)[-1]
PER_PAGE = 24


def esc(v):
    return html_escape(str(v), quote=True)


def item_data_attrs(it):
    """data-* named after the taxonomy / ACF keys. The mockup's listing.js filters, sorts and searches on these;
    in WordPress the server does that, so these are optional there."""
    pairs = [("machine-type", tax(it, "machine_type")), ("machine-brand", tax(it, "machine_brand"))]
    for k in ("model", "year", "working_height", "capacity", "outreach", "origin", "sold_to", "sold_date", "availability"):
        v = acf(it, k)
        if v is not None:
            pairs.append((k.replace("_", "-"), f"{v:g}" if isinstance(v, float) else v))
    return " ".join(f'data-{k}="{esc(v)}"' for k, v in pairs)


def sold_pic(it, cls="ratio-4-3", eager=False, label="Model photo"):
    """Model photo for a sold record (greyed by .is-sold on cards), or a placeholder when we have no photo of the model."""
    img = acf(it, "image")
    tname = TYPES[tax(it, "machine_type")][1].lower()
    if not img:
        ph = " ph--scissor" if TYPES[tax(it, "machine_type")][0] == "scissor" else ""
        return f'<div class="ph {cls} ph--req{ph}" data-label="No photo of this model yet"></div>'
    name = img if eager and (IMG / f"{img}.webp").exists() else img + "-sm"
    fit = " contain" if img in CONTAIN else ""
    return media(name, f"{acf(it, 'model')} {tname} – model photo, sold machine", cls + fit, eager, label)


# ------------------------------------------------------------------ template-parts/machine-card.php
# get_template_part('template-parts/machine-card', null, ['variant' => 'rental'|'used'|'sold'])
def machine_card(it, variant=None, hidden=False):
    variant = variant or tax(it, "listing_status")
    href = machine_href(it)
    m = acf(it, "model")
    actions = '<div class="machine-actions cpe-card__actions">{}</div>'
    btn = '<a class="btn {} btn--sm cpe-card__action" href="{}">{}</a>'
    qbtn = '<a class="btn btn--red btn--sm cpe-card__action" href="contact.html#enquiry" {}>{}</a>'
    if variant == "rental":
        c = SLUG_CAT[tax(it, "machine_type")]
        img, ph, out = acf(it, "image"), acf(it, "platform_height"), acf(it, "outreach")
        fit = " contain" if img in CONTAIN else ""
        top = f'<div class="card-top-badges">{STATUS[acf(it, "availability")]}</div>\n  '
        pic = media(img + "-sm", f"{m} {c['one'].lower()} for rent in Dubai", "ratio-4-3" + fit)
        title, type_line = m, f"{c['one']} · {acf(it, 'power')}"
        mid = f"<div><strong>{ph:g} m</strong>Platform ht.</div>" if ph else f"<div><strong>{out:g} m</strong>Outreach</div>"
        specs = (f"<div><strong>{acf(it, 'working_height'):g} m</strong>Working ht.</div>\n      {mid}\n"
                 f"      <div><strong>{acf(it, 'capacity')} kg</strong>Capacity</div>")
        price = ""
        acts = btn.format("btn--ghost", href, "Details") + "\n      " + qbtn.format(quote_attrs("rental", m, c["one"].capitalize()), "Get a Quote")
    else:
        y, origin = acf(it, "year"), acf(it, "origin")
        tname = TYPES[tax(it, "machine_type")][1]
        title, type_line = f"{y} {m}", f"{tname} · Origin: {origin}"
        if variant == "sold":
            top = '<div class="card-top-badges"><span class="badge badge--sold">Sold</span></div>\n  '
            pic = sold_pic(it)
            specs = (f"<div><strong>{y}</strong>Year</div>\n      <div><strong>{acf(it, 'sold_to') or '—'}</strong>Sold to</div>\n"
                     f"      <div><strong>{fmt_date(acf(it, 'sold_date'))}</strong>Sold</div>")
            price = ""
            acts = btn.format("btn--ghost", href, "Details") + "\n      " + qbtn.format(quote_attrs("sale", m, sold=True), "Find Me One")
        else:
            img = acf(it, "image")
            top = ""
            pic = (media(img + "-sm", f"Used {y} {m} {tname.lower()} for sale", "ratio-4-3") if img
                   else '<div class="ph ratio-4-3 ph--req" data-label="Photos on request"></div>')
            specs = (f"<div><strong>{y}</strong>Year</div>\n      <div><strong>{acf(it, 'working_height'):g} m</strong>Working ht.</div>\n"
                     f"      <div><strong>{BRAND_NAMES[tax(it, 'machine_brand')]}</strong>Brand</div>")
            price = '\n    <div class="price">Contact for price <small>UAE &amp; export enquiries</small></div>'
            acts = btn.format("btn--ghost", href, "Details") + "\n      " + qbtn.format(quote_attrs("sale", f"{y} {m}"), "Enquire")
    sold_cls = " is-sold" if variant == "sold" else ""
    return f'''<article class="machine-card{sold_cls} cpe-card cpe-card--{variant}" data-cpe-item {item_data_attrs(it)}{" hidden" if hidden else ""}>
  {top}{pic}
  <div class="machine-card-body cpe-card__body">
    <div>
      <h3 class="cpe-card__title"><a href="{href}">{title}</a></h3>
      <div class="machine-type cpe-card__type">{type_line}</div>
    </div>
    <div class="spec-mini cpe-card__specs">
      {specs}
    </div>{price}
    {actions.format(chr(10) + "      " + acts + chr(10) + "    ")}
  </div>
</article>'''


# ------------------------------------------------------------------ listing: filters, params, sorting
# URL param -> (field, kind). Mirrors FIELDS in assets/js/listing.js and the table in WORDPRESS-MAP.md.
#   tax   = taxonomy term slug        range = numeric 'min-max' (min inclusive, max exclusive, open ends empty)
#   slug  = slug of an ACF text value  year  = first 4 characters of a 'YYYY-MM' date
#   Empty text / date fields match the value 'not-recorded'.
FIELDS = {
    "m_type": ("machine_type", "tax"), "m_brand": ("machine_brand", "tax"),
    "m_year": ("year", "range"), "m_height": ("working_height", "range"),
    "m_capacity": ("capacity", "range"), "m_outreach": ("outreach", "range"),
    "m_origin": ("origin", "slug"), "m_sold_to": ("sold_to", "slug"),
    "m_sold_year": ("sold_date", "year"), "m_availability": ("availability", "slug"),
}
OPEN_TOP = (99, 2100, 9999)   # band upper bounds that mean "and above"


def rng(lo, hi):
    """Band (lo, hi) -> range param value: (0, 20) -> '-20', (20, 30) -> '20-30', (30, 99) -> '30-'."""
    return f"{'' if lo <= 0 else f'{lo:g}'}-{'' if hi in OPEN_TOP else f'{hi:g}'}"


def band_options(bands):
    return [(rng(lo, hi), label) for lo, hi, label in bands]


def facet_matches(it, param, value):
    key, kind = FIELDS[param]
    if kind == "tax":
        return tax(it, key) == value
    v = acf(it, key)
    if kind == "range":
        a, b = value.split("-")
        return v is not None and (a == "" or v >= float(a)) and (b == "" or v < float(b))
    if kind == "year":
        return (v[:4] if v else "not-recorded") == value
    return (slug(str(v)) if v else "not-recorded") == value


def sort_items(items, sort):
    """m_sort 'field-dir' -> items sorted on that ACF field (stable; mirrors sortItems() in listing.js)."""
    field, direction = sort.rsplit("-", 1)

    def key(it):
        v = acf(it, field)
        return 0 if v is None else float(str(v).replace("-", ""))
    return sorted(items, key=key, reverse=direction == "desc")


def listing_ctx(page_type, items, groups, sorts, nouns=("machine", "machines"), search=None, tries=(), note="",
                label="machines"):
    """ctx shared by all listing template parts (WordPress: the $args passed to each get_template_part()).
    groups: [(title, param, [(value, label), ...])] – counts are computed here, options with no items are dropped."""
    fgroups = []
    for title, param, options in groups:
        opts = [(v, lab, sum(facet_matches(it, param, v) for it in items)) for v, lab in options]
        fgroups.append((title, param, [o for o in opts if o[2]]))
    return dict(page_type=page_type, items=sort_items(items, sorts[0][0]), groups=fgroups, sorts=sorts,
                total=len(items), per_page=PER_PAGE, paged=1, nouns=nouns, search=search, tries=tries, note=note,
                label=label)


def count_label(n, nouns):
    return f"{n} {nouns[0] if n == 1 else nouns[1]}"


def results_heading(total, paged, per_page, nouns):
    """'Showing 25–48 of 212 records' (mirrors headingText() in listing.js)."""
    if total <= per_page:
        return f"Showing {count_label(total, nouns)}"
    a = (paged - 1) * per_page + 1
    return f"Showing {a}–{min(total, paged * per_page)} of {count_label(total, nouns)}"


RENTAL_SORTS = [("working_height-asc", "Working height (low to high)"), ("working_height-desc", "Working height (high to low)"),
                ("capacity-desc", "Capacity (highest first)")]


# ------------------------------------------------------------------ template-parts/listing-filters.php
def listing_filters(ctx):
    groups = "".join(
        f'<div class="filter-group cpe-listing-filters__group" role="group" aria-labelledby="cpe-g-{param}">'
        f'<h3 id="cpe-g-{param}">{title}</h3>'
        + "".join(f'<label data-label="{lab}"><input type="checkbox" name="{param}" value="{v}"> {lab} <span class="count">{n}</span></label>'
                  for v, lab, n in opts)
        + "</div>"
        for title, param, opts in ctx["groups"])
    return f'''<form id="cpe-filters" class="filters cpe-listing-filters" method="get" aria-label="Filter {ctx["label"]}" data-cpe-filters>
      <div class="filters-head"><h2>Filter</h2><div class="filters-head-actions"><a href="?" data-cpe-clear-all>Clear all</a><button type="button" class="filters-x" data-cpe-filter-close aria-label="Close filters">&times;</button></div></div>
      {groups}
      <div class="filter-close cpe-listing-filters__apply"><button type="submit" class="btn btn--red btn--block" data-cpe-filter-apply>Show {count_label(ctx["total"], ctx["nouns"])}</button></div>
    </form>'''


# ------------------------------------------------------------------ template-parts/listing-toolbar.php
def listing_toolbar(ctx):
    opts = "".join(f'<option value="{v}">{l}</option>' for v, l in ctx["sorts"])
    search = ""
    if ctx["search"]:
        search = f'''<div class="cpe-listing-search" role="search">
          <label class="sr-only" for="cpe-q">Search machines</label>
          <span class="cpe-listing-search__icon">{icon("search")}</span>
          <input id="cpe-q" class="cpe-listing-search__input" type="search" name="q" form="cpe-filters" placeholder="{ctx["search"]}" aria-label="Search machines" autocomplete="off" spellcheck="false" data-cpe-search>
          <button type="button" class="cpe-listing-search__clear" aria-label="Clear search" data-cpe-search-clear hidden>&times;</button>
        </div>
        '''
    return f'''<div class="cpe-listing-toolbar">
        {search}<div class="cpe-listing-toolbar__actions">
          <button type="button" class="btn btn--ghost btn--sm filter-open" data-cpe-filter-open>{icon("filter")} Filter</button>
          <label class="sort-group"><span class="sort-label">Sort by:</span><select class="select cpe-listing-toolbar__sort" name="m_sort" form="cpe-filters" data-cpe-sort>{opts}</select></label>
        </div>
      </div>
      <div class="active-chips cpe-listing-chips" data-cpe-chips></div>'''


# ------------------------------------------------------------------ template-parts/listing-empty.php
# The server renders the final title/links for the current search. The data-* templates are only for the mockup's JS.
EMPTY_COPY = {
    "used": dict(title="No machines match these filters", title_term="No {term} in stock right now",
                 text="We source used JLG and Genie lifts on request. Tell us the spec and we'll find one for you.",
                 wa="Hi Cherry Pickers, I'm looking for a used machine. Do you have one or can you source it?",
                 wa_term="Hi Cherry Pickers, I'm looking for a used {term}. Do you have one or can you source it?", need="buy"),
    "sold": dict(title="No records match these filters", title_term="No sold records for {term}",
                 text="We source used JLG and Genie lifts on request. Tell us the spec and we'll find one for you.",
                 wa="Hi Cherry Pickers, I'm looking for a machine like the ones you've sold. Can you source one?",
                 wa_term="Hi Cherry Pickers, I'm looking for a {term} like the ones you've sold. Can you source one?", need="buy"),
    "rental": dict(title="No machines match these filters", title_term="No {term} in our rental fleet right now",
                   text="Tell us the working height and the job, and we'll suggest the right machine.",
                   wa="Hi Cherry Pickers, I'd like a rental quote.",
                   wa_term="Hi Cherry Pickers, I'd like to rent a {term}. Is one available?", need="rent"),
}


def listing_empty(ctx):
    c = EMPTY_COPY[ctx["page_type"]]
    tries = "".join(f'<button type="button" class="chip" data-cpe-try="{esc(t)}">{esc(t)}</button>' for t in ctx["tries"])
    try_html = f'\n    <p class="cpe-listing-empty__try"><span>Try:</span> {tries}</p>' if tries and ctx["search"] else ""
    return f'''<div class="empty-state cpe-listing-empty" data-cpe-empty hidden data-title="{esc(c["title"])}" data-title-term="{esc(c["title_term"])}" data-wa="{esc(c["wa"])}" data-wa-term="{esc(c["wa_term"])}">
    <h3 class="cpe-listing-empty__title" data-cpe-empty-title>{c["title"]}</h3>
    <p class="cpe-listing-empty__text">{c["text"]}</p>
    <div class="cpe-listing-empty__actions">
      <a class="btn btn--red" href="contact.html?need={c["need"]}#enquiry" {quote_attrs({"rent": "rental", "buy": "sale"}[c["need"]])} data-cpe-empty-quote>Tell us your spec</a>
      <a class="btn btn--wa" href="{wa_url(c["wa"])}" data-cpe-empty-wa>{icon("wa")} WhatsApp</a>
      <button type="button" class="btn btn--ghost" data-cpe-clear-filters hidden>Clear filters</button>
    </div>{try_html}
  </div>'''


# ------------------------------------------------------------------ template-parts/pagination.php
def page_list(cur, last):
    """1 … 4 5 6 … 9 (None = gap). A gap of exactly one page shows that page instead (mirrors pageList() in listing.js)."""
    keep = sorted(p for p in {1, last, cur - 1, cur, cur + 1} if 1 <= p <= last)
    out, prev = [], 0
    for p in keep:
        if p - prev == 2:
            out.append(prev + 1)
        elif p - prev > 2:
            out.append(None)
        out.append(p)
        prev = p
    return out


def listing_pagination(ctx, query=""):
    """Real links: ?<current params>&paged=N (page 1 drops paged). Nothing when everything fits on one page."""
    total, per, cur = ctx["total"], ctx["per_page"], ctx["paged"]
    last = -(-total // per)
    if last <= 1:
        return ""

    def href(p):
        q = "&amp;".join(x for x in (query, f"paged={p}" if p > 1 else "") if x)
        return f"?{q}"
    lab = '<span class="cpe-listing-pagination__label">{}</span>'
    prev = (f'<a class="cpe-listing-pagination__prev" href="{href(cur - 1)}" rel="prev" data-cpe-page="{cur - 1}">‹ {lab.format("Previous")}</a>'
            if cur > 1 else f'<span class="cpe-listing-pagination__prev is-disabled" aria-disabled="true">‹ {lab.format("Previous")}</span>')
    nxt = (f'<a class="cpe-listing-pagination__next" href="{href(cur + 1)}" rel="next" data-cpe-page="{cur + 1}">{lab.format("Next")} ›</a>'
           if cur < last else f'<span class="cpe-listing-pagination__next is-disabled" aria-disabled="true">{lab.format("Next")} ›</span>')
    pages = "".join(
        '<li><span class="cpe-listing-pagination__gap" aria-hidden="true">…</span></li>' if p is None else
        (f'<li><span class="cpe-listing-pagination__page is-current" aria-current="page">{p}</span></li>' if p == cur else
         f'<li><a class="cpe-listing-pagination__page" href="{href(p)}" data-cpe-page="{p}" aria-label="Page {p}">{p}</a></li>')
        for p in page_list(cur, last))
    return f'''<nav class="cpe-listing-pagination" aria-label="Pagination">
      {prev}
      <ul class="cpe-listing-pagination__pages">{pages}</ul>
      <span class="cpe-listing-pagination__status">Page {cur} of {last}</span>
      {nxt}
    </nav>'''


# ------------------------------------------------------------------ archive-machine.php: results region
# WordPress swaps this whole element (#cpe-results) with the fetched response. Keep everything that depends on the
# result set inside it: heading/count, cards, empty state, pagination.
def listing_results(ctx):
    per = ctx["per_page"]
    cards = "".join(machine_card(it, ctx["page_type"], hidden=n >= per)
                    for n, it in enumerate(ctx["items"]))
    return f'''<div id="cpe-results" class="cpe-listing-results" data-total="{ctx["total"]}" data-paged="1">
        <h2 class="cpe-listing-results__heading" tabindex="-1" data-cpe-heading>{results_heading(ctx["total"], 1, per, ctx["nouns"])}</h2>
        <div class="grid grid-3 cpe-listing-results__grid" data-cpe-grid>
          {"".join(cards)}
        </div>
        {listing_empty(ctx)}
        <div class="cpe-listing-results__pager" data-cpe-pager>{listing_pagination(ctx)}</div>
      </div>'''


# Front-end config for the current page (WordPress: wp_localize_script('cpe-listing', 'CPE', [...])).
# listing() sets it; build() prints it in <head> and adds listing.js. Reset by build() for every page.
CPE_PAGE = None
# Structured data for the current page: a page function sets dict(faq=[(q, a), ...]); build() then prints
# BreadcrumbList + FAQPage JSON-LD in <head>. Reset by build() for every page.
PAGE_LD = None


# ------------------------------------------------------------------ archive-machine.php: listing layout
def listing(ctx):
    global CPE_PAGE
    CPE_PAGE = {"whatsapp": WA_NUMBER, "pageType": ctx["page_type"], "perPage": ctx["per_page"],
                "nouns": list(ctx["nouns"]), "search": bool(ctx["search"])}
    return f'''<div class="listing cpe-listing">
      {listing_filters(ctx)}
      <div class="cpe-listing-main">
        {listing_toolbar(ctx)}
        {listing_results(ctx)}
        <p class="sr-only" aria-live="polite" data-cpe-announce></p>
        {ctx["note"]}
      </div>
    </div>'''


def faq_html(items):
    out = []
    for n, (q, a) in enumerate(items):
        op = " open" if n == 0 else ""
        out.append(f'<details{op}><summary><h3>{q}</h3></summary><div><p>{a}</p></div></details>')
    return '<div class="faq">' + "".join(out) + "</div>"


# ================================================================== RENTAL: shared parts
# template-parts/category-card.php – image card for a main category (group) or a sub-category
def cat_tile(c):
    """Card for a sub-category (child machine_type term) – links to its listing page."""
    return f'''<a class="tile" href="{c['file']}">
        {media(c['img'] + '-sm', c['one'] + ' rental in Dubai', 'tile-img')}
        <div class="tile-body">
          <span class="tile-meta">{c['n']} models · {c['range']}</span>
          <h3>{c['name']}</h3>
          <p>{c['short']}</p>
          <span class="tile-link">View {c['name'].lower()} →</span>
        </div>
      </a>'''


def group_tile(g):
    """Card for a main category (parent machine_type term) – links to its main-category page."""
    meta = f"Coming soon · {g['range']}" if g.get("soon") else f"{g['n']} models · {g['range']}"
    link = f"About {g['name'].lower()} →" if g.get("soon") else f"View {g['name'].lower()} →"
    return f'''<a class="tile" href="{g['file']}">
        {media(g['img'] + '-sm', g['one'] + ' rental in Dubai', 'tile-img')}
        <div class="tile-body">
          <span class="tile-meta">{meta}</span>
          <h3>{g['name']}</h3>
          <p>{g['short']}</p>
          <span class="tile-link">{link}</span>
        </div>
      </a>'''


def rental_options_html():
    return f'''<!-- RENTAL OPTIONS -->
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
</section>'''


def spec_span(items, field, unit):
    """'15.7 – 28.2 m' over the machines' values of an ACF field ('—' when none recorded)."""
    vals = [acf(it, field) for it in items if acf(it, field) is not None]
    if not vals:
        return "—"
    lo, hi = min(vals), max(vals)
    if unit == "m":
        lo, hi = r1(lo), r1(hi)
    return f"{lo:g} {unit}" if lo == hi else f"{lo:g} – {hi:g} {unit}"


GUIDE_LINKS = [("Boom Lift vs Scissor Lift: How to Choose", "blog-detail.html"),
               ("Articulated vs Telescopic Boom Lift", "blog-detail.html"),
               ("Working Height vs Platform Height Explained", "blog-detail.html")]


# ================================================================== RENTAL LANDING
def page_rental_landing():
    tiles = [group_tile(g) for g in GROUPS.values()]
    # height finder table
    bands = RENTAL_BANDS
    rows = []
    for lo, hi, lab in bands:
        cells = []
        for c in CATS.values():
            ms = [it for it in c["models"] if lo <= acf(it, "working_height") < hi]
            if ms:
                cells.append(f'<a href="{c["file"]}"><strong>{c["name"]}</strong></a><br><span class="small muted">{", ".join(acf(it, "model") for it in ms)}</span>')
        rows.append(f'<tr><td><strong>{lab}</strong></td><td>{"<hr class=\"cell-hr\">".join(cells)}</td></tr>')
    sp = GROUPS["spider"]
    faq = [
        ("What access equipment can I rent from Cherry Pickers Equipment?", f"We rent {N_RENTAL} models of boom lifts (telescopic, articulated and electric) and scissor lifts (slab electric, rough terrain electric and diesel 4x4), from 7.8 m to 43 m working height. Spider lifts from {sp['lo']} to {sp['hi']} are coming soon."),
        sp["faq"][0],
        ("What is the minimum rental period?", "You can rent for a single day. We also offer weekly, monthly and long-term hire."),
        ("Do you deliver outside Dubai?", "Yes. We deliver and collect across all seven emirates: Dubai, Abu Dhabi, Sharjah, Ajman, Ras Al Khaimah, Fujairah and Umm Al Quwain."),
        ("Do you supply operators?", "Yes, on request. Tell us when you book and we will include an operator with the machine."),
        ("How do I choose between a scissor lift and a boom lift?", "Choose a scissor lift to go straight up with a large platform. Choose a boom lift when you need to reach up and out, or over obstacles."),
    ]
    sc, bm = GROUPS["scissor"], GROUPS["boom"]
    sc_links = " &nbsp; ".join(f'<a class="link-arrow" href="{c["file"]}">{c["menu"]} →</a>' for c in sc["cats"])
    bm_links = " &nbsp; ".join(f'<a class="link-arrow" style="color:#ff5a45" href="{c["file"]}">{c["menu"]} →</a>' for c in bm["cats"])
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

<!-- 2. MAIN CATEGORY TILES: each links to /rental/{{main category}}/ (which lists its sub-categories) -->
<section class="section" id="categories">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Choose a machine type</span>
      <h2>Our Rental Equipment Categories</h2>
      <p>Pick a category to see its machine types, then filter to the machine that fits your job by working height, outreach and capacity.</p>
    </div>
    <div class="tiles tiles--3">
      {"".join(tiles)}
    </div>
    <p class="mt-24"><a class="link-arrow" href="rental-all.html">Browse all {N_RENTAL} rental machines with filters →</a></p>
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
          <li>Indoors on smooth floors (slab electric) or outdoors on rough ground (rough terrain electric, diesel 4x4)</li>
        </ul>
        <p><a class="link-arrow" href="{sc['file']}">All scissor lifts →</a></p>
        {sc_links}
      </div>
      <div class="split-panel split-panel--navy">
        <h3 style="font-size:1.5rem">Choose a boom lift when…</h3>
        <ul class="tick-list">
          <li>You need to reach <strong>up and out</strong>, away from the base</li>
          <li>Obstacles are in the way (articulated)</li>
          <li>You need the longest straight reach (telescopic)</li>
          <li>Quiet, zero-emission work indoors (electric boom)</li>
        </ul>
        <p><a class="link-arrow" style="color:#ff5a45" href="{bm['file']}">All boom lifts →</a></p>
        {bm_links}
      </div>
      <div class="split-panel">
        <h3 style="font-size:1.5rem">Choose a spider lift when…</h3>
        <ul class="tick-list">{"".join(f"<li>{x}</li>" for x in sp["when"]["spider"])}</ul>
        <a class="link-arrow" href="{sp['file']}">Spider lifts – coming soon →</a>
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
      {"".join(f'<a class="chip" href="{u}">{t}</a>' for t, u in GUIDE_LINKS)}
    </div>
  </div>
</section>

{{{{cta:Need a Machine for Your Project?|Tell us the working height, the job and the site location. We'll suggest the right machine and send a quote.}}}}
'''


# ================================================================== RENTAL MAIN CATEGORY (/rental/{main}/)
# WordPress: taxonomy-machine_type.php for a parent term – content + one category card per child term.
def page_rental_group(g):
    global PAGE_LD
    PAGE_LD = dict(faq=g["faq"])   # build(): BreadcrumbList + FAQPage JSON-LD in <head>
    soon = g.get("soon")
    intro = g["intro"].format(n=g["n"], lo=g["lo"], hi=g["hi"])
    others = [o for o in GROUPS.values() if o["key"] != g["key"]]
    if soon:
        qa = quote_attrs("rental", category=QUOTE_CATEGORIES[-1])
        actions = f'''<a class="btn btn--red" href="contact.html#enquiry" {qa}>Register Interest</a>
      <a class="btn btn--wa" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp Us</a>'''
        eyebrow = f"Coming soon · {g['range']} working height"
    else:
        actions = f'''<a class="btn btn--red" href="contact.html#enquiry" {quote_attrs("rental")}>Get a Quote</a>
      <a class="btn btn--wa" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp</a>
      <a class="btn btn--ghost-light" href="#types">See the {len(g["cats"])} types</a>'''
        eyebrow = f"{g['name']} for rent · UAE"
    hero = f'''<!-- 1. HERO: full-width photo + answer-first intro -->
<section class="r-hero">
  {hero_img(g["img"], g["one"] + " for rent in Dubai")}
  <div class="wrap r-hero-inner">
    <span class="eyebrow">{eyebrow}</span>
    <h1>{g["h1"]}</h1>
    <p class="hero-lead">{intro}</p>
    <div class="hero-actions">
      {actions}
    </div>
  </div>
</section>'''

    if soon:
        types = f'''<!-- 2. COMING SOON: no sub-categories yet (WordPress: term meta status=coming-soon, height_range) -->
<section class="section" id="types">
  <div class="wrap">
    <div class="split-panel split-panel--navy">
      <span class="eyebrow" style="color:#ff5a45">Coming soon</span>
      <h2>{g["name"]} from {g["lo"]} to {g["hi"]} Working Height</h2>
      <p>Tracked spider lifts are joining our rental fleet soon. Register your interest and we'll contact you first with the models, dates and prices – or ask us now which machine in our current fleet suits your site.</p>
      <div class="hero-actions" style="margin-bottom:0">
        <a class="btn btn--red" href="contact.html#enquiry" {quote_attrs("rental", category=QUOTE_CATEGORIES[-1])}>Register Interest</a>
        <a class="btn btn--ghost-light" href="rental-all.html">See our current fleet</a>
      </div>
    </div>
  </div>
</section>

<!-- 3. WHEN TO CHOOSE + BEST USES -->
<section class="section section--alt">
  <div class="wrap grid grid-2" style="gap:56px;align-items:start">
    <div class="split-panel">
      <h2 style="font-size:1.5rem">Choose a spider lift when…</h2>
      <ul class="tick-list">{"".join(f"<li>{x}</li>" for x in g["when"]["spider"])}</ul>
    </div>
    <div class="content">
      <h2>Best Uses for {g["name"]}</h2>
      <ul class="tick-list">{"".join(f"<li>{u}</li>" for u in g["uses"])}</ul>
    </div>
  </div>
</section>'''
    else:
        ck, clabel = g["cmp"]
        rows = "".join(
            f'<tr><td><a href="{c["file"]}"><strong>{c["name"]}</strong></a><br><span class="small muted">{c["n"]} models</span></td>'
            f'<td>{spec_span(c["models"], "working_height", "m")}</td><td>{spec_span(c["models"], ck, "m")}</td>'
            f'<td>{spec_span(c["models"], "capacity", "kg")}</td><td>{" / ".join(sorted({acf(it, "power") for it in c["models"]}))}</td></tr>'
            for c in g["cats"])
        panels = []
        for i, c in enumerate(g["cats"]):
            navy = i == 1
            lk = ' style="color:#ff5a45"' if navy else ""
            panels.append(f'''<div class="split-panel{" split-panel--navy" if navy else ""}">
        <h3 style="font-size:1.4rem">Choose {c["name"].lower()} when…</h3>
        <ul class="tick-list">{"".join(f"<li>{x}</li>" for x in g["when"][c["key"]])}</ul>
        <a class="link-arrow"{lk} href="{c["file"]}">View {c["n"]} {c["menu"].lower()} models →</a>
      </div>''')
        types_q = ",".join(c["slug"] for c in g["cats"])
        types = f'''<!-- 2. SUB-CATEGORY CARDS: each links to /rental/{g["slug"]}/{{sub category}}/ (listing with filters) -->
<section class="section" id="types">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Choose a type</span>
      <h2>Types of {g["name"]} We Rent</h2>
      <p>Open a type to see every machine with working height, {clabel.lower()} and capacity – and filter to the one that fits your job.</p>
    </div>
    <div class="tiles tiles--3">
      {"".join(cat_tile(c) for c in g["cats"])}
    </div>
    <p class="mt-24"><a class="link-arrow" href="rental-all.html?m_type={types_q}">Browse all {g["n"]} {g["name"].lower()} with filters →</a></p>
  </div>
</section>

<!-- 3. COMPARE THE TYPES: answer-style table, computed from the fleet -->
<section class="section section--alt">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">Compare</span>
      <h2>{g["name"]} Compared</h2>
      <p>Ranges across the machines in our rental fleet.</p>
    </div>
    <div class="table-wrap">
      <table class="finder">
        <thead><tr><th>Type</th><th>Working height</th><th>{clabel}</th><th>Capacity</th><th>Power</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>
</section>

<!-- 4. HOW TO CHOOSE + BEST USES -->
<section class="section">
  <div class="wrap">
    <div class="section-head section-head--center">
      <span class="eyebrow">Quick guide</span>
      <h2>Which {g["one"]} Do I Need?</h2>
    </div>
    <div class="grid grid-3 guide-3">
      {"".join(panels)}
    </div>
    <div class="grid grid-2 mt-40" style="gap:56px;align-items:center">
      <div class="content">
        <h2>Best Uses for {g["name"]}</h2>
        <ul class="tick-list">{"".join(f"<li>{u}</li>" for u in g["uses"])}</ul>
      </div>
      {media(g["img"] + "-sm", g["one"] + " at work", "ratio-16-9")}
    </div>
  </div>
</section>

{rental_options_html()}'''

    cta = ("{{cta:Register Interest in Spider Lifts|Tell us the working height, the site and when you need it. We'll contact you as soon as our spider lifts arrive.}}"
           if soon else f"{{{{cta:Get a Quote for {g['name']}|Tell us the working height, site location and dates. We'll confirm the right machine and send your quote.}}}}")
    return f'''{hero}

{types}

<!-- FAQ (also FAQPage JSON-LD in <head>) -->
<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Questions</span><h2>{g["one"]} Rental Questions</h2></div>
    {faq_html(g["faq"])}
  </div>
</section>

<!-- RELATED: the other main categories, landing page and guides -->
<section class="section section--alt section--tight">
  <div class="wrap grid grid-2" style="gap:40px">
    <div>
      <h2 style="font-size:1.5rem">Other Rental Machines</h2>
      <div class="cat-chips">{"".join(f'<a class="chip" href="{o["file"]}">{o["name"]}{" (coming soon)" if o.get("soon") else ""}</a>' for o in others)}<a class="chip" href="rental-all.html">All rental machines</a><a class="chip" href="rental.html">All rental equipment</a></div>
    </div>
    <div>
      <h2 style="font-size:1.5rem">Related Guides</h2>
      <ul class="tick-list mt-24">{"".join(f'<li><a href="{u}">{t}</a></li>' for t, u in GUIDE_LINKS[:2])}</ul>
    </div>
  </div>
</section>

{cta}
'''


# ================================================================== ALL RENTAL MACHINES (/rental/all-machines/)
# The home page machine finder lands here with ?m_type=<machine_type>&m_height=<min-max>
RENTAL_BANDS = [(0, 10, "Up to 10 m"), (10, 16, "10 – 16 m"), (16, 22, "16 – 22 m"), (22, 99, "22 m and above")]


def page_rental_all():
    fleet = listing_ctx("rental", sorted(RENTAL_ITEMS, key=lambda it: acf(it, "working_height")), [
        ("Machine type", "m_type", [(c["slug"], c["name"]) for c in CATS.values()]),
        ("Working height", "m_height", band_options(RENTAL_BANDS)),
        ("Brand", "m_brand", [(b, BRAND_NAMES[b]) for b in sorted({tax(it, "machine_brand") for it in RENTAL_ITEMS})]),
    ], RENTAL_SORTS)
    switch = "".join(f'<a class="chip" href="{g["file"]}">{g["name"]} ({"coming soon" if g.get("soon") else g["n"]})</a>' for g in GROUPS.values())
    return f'''<!-- 1. COMPACT HEADER: H1 + intro + main-category chips (listing comes first on this page) -->
<section class="r-hero r-hero--compact">
  {hero_img("cat-articulated", "Boom lifts and scissor lifts for rent in Dubai")}
  <div class="wrap r-hero-inner">
    <div class="listing-hero-grid">
      <div>
        <h1>All Rental Machines</h1>
        <p class="lead">Our full rental fleet: {N_RENTAL} scissor lift and boom lift models from 7.8 m to 43 m working height. Filter by machine type, working height and brand.</p>
      </div>
      <div class="listing-hero-cta">
        <a class="btn btn--red btn--block" href="contact.html#enquiry" {quote_attrs("rental")}>Get a Quote</a>
        <a class="btn btn--wa btn--block" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp</a>
      </div>
    </div>
    <nav class="cat-chips" aria-label="Rental categories">{switch}</nav>
  </div>
</section>

<!-- 2. FULL FLEET LISTING (filter URLs: canonical = the clean /rental/all-machines/ URL, never in the sitemap) -->
<section class="section" id="all-machines" style="padding-top:32px">
  <div class="wrap">
    {listing(fleet)}
  </div>
</section>
'''


# ================================================================== RENTAL SUB-CATEGORY LISTING (/rental/{main}/{sub}/)
def page_rental_category(c):
    g = c["group"]
    ms = sorted(c["models"], key=lambda it: acf(it, "working_height"))
    skey, stitle, sbands = c["second"]
    brands = Counter(tax(it, "machine_brand") for it in ms)
    # "Try:" chips: lowest and highest model (without the brand) + the most common brand
    short = [acf(it, "model").split(" ", 1)[1] for it in (ms[0], ms[-1])]
    tries = list(dict.fromkeys(short + [BRAND_NAMES[brands.most_common(1)[0][0]]]))
    ctx = listing_ctx("rental", ms, [
        ("Working height", "m_height", band_options(c["hb"])),
        (stitle, {"cap": "m_capacity", "out": "m_outreach"}[skey], band_options(sbands)),
        ("Brand", "m_brand", [(b, BRAND_NAMES[b]) for b in sorted(brands)]),
        ("Availability", "m_availability", [("available", "Available now"), ("on-hire", "On hire")]),
    ], RENTAL_SORTS, search=f"Search model, e.g. {short[0]}" if c["search"] else None, tries=tries)
    # switcher: the sub-categories of this main category (+ back to the main category page)
    switch = f'<a class="chip" href="{g["file"]}">← All {g["name"].lower()}</a>' + "".join(
        f'<a class="chip{" chip--active" if o["key"] == c["key"] else ""}" href="{o["file"]}">{o["name"]} ({o["n"]})</a>'
        for o in g["cats"])
    others = ("".join(f'<a class="chip" href="{o["file"]}">{o["name"]}</a>' for o in g["cats"] if o["key"] != c["key"])
              + "".join(f'<a class="chip" href="{o["file"]}">{o["name"]}{" (coming soon)" if o.get("soon") else ""}</a>'
                        for o in GROUPS.values() if o["key"] != g["key"]))
    choose = "".join(f"<p><strong>{t}:</strong> {x}</p>" for t, x in c["choose"])
    intro = c["intro"].format(n=c["n"], lo=c["lo"], hi=c["hi"])
    return f'''<!-- 1. COMPACT HEADER: H1 + answer-first intro + sub-category switcher (listing comes first on this page) -->
<section class="r-hero r-hero--compact">
  {hero_img(c["img"], c["one"] + " for rent in Dubai")}
  <div class="wrap r-hero-inner">
    <div class="listing-hero-grid">
      <div>
        <h1>{c["h1"]}</h1>
        <p class="lead">{intro}</p>
      </div>
      <div class="listing-hero-cta">
        <a class="btn btn--red btn--block" href="contact.html#enquiry" {quote_attrs("rental", category=c["one"].capitalize())}>Get a Quote</a>
        <a class="btn btn--wa btn--block" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp</a>
      </div>
    </div>
    <nav class="cat-chips" aria-label="{g["name"]} types">{switch}</nav>
  </div>
</section>

<!-- 2. LISTING with category-specific filters (filter URLs: canonical = the clean category URL, never in the sitemap) -->
<section class="section" style="padding-top:32px">
  <div class="wrap">
    {listing(ctx)}
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

{rental_options_html()}

<!-- 7. FAQ -->
<section class="section">
  <div class="wrap">
    <div class="section-head"><span class="eyebrow">Questions</span><h2>{c["one"]} Rental Questions</h2></div>
    {faq_html(c["faq"])}
  </div>
</section>

<!-- 8. RELATED: internal links to sibling types, other main categories, landing page and guides -->
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

{{{{cta:Get a Quote for {c["one"].lower()}s|Tell us the working height, site location and dates. We'll confirm the right model and send your quote.}}}}
'''


# ================================================================== SALES LANDING
def page_sales_landing():
    by_t = Counter(TYPES[tax(it, "machine_type")][0] for it in USED)
    sold_t = Counter(TYPES[tax(it, "machine_type")][0] for it in SOLD)
    to = Counter(acf(it, "sold_to") for it in SOLD if acf(it, "sold_to"))
    models = Counter(acf(it, "model") for it in SOLD).most_common(4)
    dated = sorted([it for it in SOLD if acf(it, "sold_date") and not acf(it, "sold_date").endswith("-00")],
                   key=lambda it: acf(it, "sold_date"), reverse=True)
    first = min(acf(it, "sold_date") for it in SOLD if acf(it, "sold_date"))
    recent = "".join(
        f'<tr><td><a href="{machine_href(it)}"><strong>{acf(it, "model")}</strong></a></td><td>{TYPES[tax(it, "machine_type")][1]}</td>'
        f'<td>{acf(it, "year")}</td><td>{acf(it, "origin")}</td><td>{acf(it, "sold_to")}</td><td>{fmt_date(acf(it, "sold_date"))}</td></tr>'
        for it in dated[:6])
    cats = [
        ("telescopic", "Telescopic Boom Lifts", "s-860sj-2004-sm", "JLG 660SJ, 860SJ, 1200SJP, 1350SJP and Genie S-65 booms."),
        ("articulated", "Articulated Boom Lifts", "s-600aj-1-sm", "JLG 600AJ and electric E450AJ / M450AJ booms."),
        ("scissor", "Scissor Lifts", "cat-rt-scissor-sm", "Genie GS-4047 and GS-5390 RT scissors – sourced on request."),
    ]
    tiles = []
    for v, name, img, txt in cats:
        avail = by_t.get(v, 0)
        # used and sold listings both filter by ?m_type= (machine_type slugs, same values as the home finder; comma = several)
        cats = ",".join(k for k, (tv, _) in TYPES.items() if tv == v)
        href = f"sales-used.html?m_type={cats}" if avail else f"sales-sold.html?m_type={cats}"
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
    <p class="hero-lead">Cherry Pickers Equipment buys and sells used access equipment from JLG and Genie. We have {len(USED)} machines available now and have sold {N_SOLD} machines since {fmt_date(first)}, mostly to buyers in India and Vietnam.</p>
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
      <span class="path-num">{len(USED)}</span>
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
      <a{cls("used")} href="sales-used.html">Used <span class="count">{len(USED)}</span></a>
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
        <a class="btn btn--red btn--block" href="contact.html#enquiry" {quote_attrs("sale")}>Send an Enquiry</a>
        <a class="btn btn--wa btn--block" href="{{{{WA_LINK}}}}">{icon("wa")} WhatsApp Sales</a>
      </div>
    </div>
    {extra}
  </div>
</section>'''


def sale_listing(rows, note="", search=False):
    """Filters + toolbar + results for machines for sale (used, or new once NEW has items)."""
    ybands = [(2015, 2100, "2015 and newer"), (2008, 2015, "2008 – 2014"), (0, 2008, "2007 and older")]
    hbands = [(0, 20, "Up to 20 m"), (20, 30, "20 – 30 m"), (30, 99, "30 m and above")]
    origins = sorted({acf(it, "origin") for it in rows})
    ctx = listing_ctx("used", rows, [
        ("Machine type", "m_type", [(c["slug"], c["one"]) for c in CATS.values()]),
        ("Brand", "m_brand", [("jlg", "JLG"), ("genie", "Genie")]),
        ("Year", "m_year", band_options(ybands)),
        ("Working height", "m_height", band_options(hbands)),
        ("Machine origin", "m_origin", [(slug(o), o) for o in origins]),
    ], [("year-desc", "Year (newest first)"), ("year-asc", "Year (oldest first)"), ("working_height-desc", "Working height (highest first)")],
        search="Search model, e.g. 860SJ" if search else None, tries=("860SJ", "E450AJ", "Genie"), note=note)
    return listing(ctx)


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
        <a class="btn btn--red" href="contact.html#enquiry" {quote_attrs("sale")}>Send an Enquiry</a>
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
    note = f'<p class="small muted mt-24">Mockup shows page 1 of your current listing ({len(USED)} machines – one duplicate listing merged). Grey cards = no reliable photo yet.</p>'
    return f'''{sales_hero("Used Access Equipment for Sale", f"{len(USED)} used boom lifts in stock from JLG and Genie, with year, origin and photos. Contact us for price, more photos or a walk-around video.", "s-600aj-1", "Used JLG 600AJ articulated boom lift for sale")}

<section class="section" style="padding-top:28px">
  <div class="wrap">
    {sales_tabs("used")}
    {sale_listing(USED, note, search=True)}
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
    """Sold records: same layout as Used (filters + toolbar + machine cards), 24 per page."""
    ybands = [(2016, 2100, "2016 and newer"), (2011, 2016, "2011 – 2015"), (2006, 2011, "2006 – 2010"), (0, 2006, "2005 and older")]
    fto = Counter(slug(acf(it, "sold_to")) if acf(it, "sold_to") else "not-recorded" for it in SOLD)
    first = min(acf(it, "sold_date") for it in SOLD if acf(it, "sold_date"))
    top = Counter(acf(it, "model") for it in SOLD).most_common(1)[0]
    origins = [o for o, _ in Counter(acf(it, "origin") for it in SOLD).most_common()]
    dests = [d for d, _ in Counter(acf(it, "sold_to") for it in SOLD if acf(it, "sold_to")).most_common()]
    years = sorted({acf(it, "sold_date")[:4] for it in SOLD if acf(it, "sold_date")}, reverse=True)
    ctx = listing_ctx("sold", SOLD, [
        ("Machine type", "m_type", [(c["slug"], c["one"]) for c in CATS.values()]),
        ("Brand", "m_brand", [("jlg", "JLG"), ("genie", "Genie")]),
        ("Sold to", "m_sold_to", [(slug(d), d) for d in dests] + [("not-recorded", "Not recorded")]),
        ("Year sold", "m_sold_year", [(y, y) for y in years] + [("not-recorded", "Not recorded")]),
        ("Model year", "m_year", band_options(ybands)),
        ("Machine origin", "m_origin", [(slug(o), o) for o in origins]),
    ], [("sold_date-desc", "Most recently sold"), ("sold_date-asc", "Oldest sales first"),
        ("year-desc", "Model year (newest first)"), ("year-asc", "Model year (oldest first)")],
        nouns=("record", "records"), label="records", search="Search model, e.g. 860SJ", tries=("860SJ", "660SJ", "Genie"),
        note='<p class="small muted mt-24">Photos are model photos from our rental fleet and sales stock, not the sold unit. Grey cards = no photo of that model yet.</p>')
    stats = f'''<div class="sold-stats">
      <div><strong>{N_SOLD}</strong><span>Machines sold</span></div>
      <div><strong>{fto["india"]}</strong><span>To India</span></div>
      <div><strong>{fto["vietnam"]}</strong><span>To Vietnam</span></div>
      <div><strong>{top[0]}</strong><span>Most sold model ({top[1]})</span></div>
    </div>'''
    lead = (f"A record of every used boom lift and scissor lift we have sold: {N_SOLD} machines since {fmt_date(first)}, "
            f"exported mainly to India ({fto['india']}) and Vietnam ({fto['vietnam']}). Looking for one like these? We can source it.")
    return f'''{sales_hero("Sold Access Equipment – Our Sales Records", lead, "s-600aj-2", "Used JLG boom lift sold and exported", stats)}

<section class="section" style="padding-top:28px">
  <div class="wrap">
    {sales_tabs("sold")}
    {listing(ctx)}
  </div>
</section>

<section class="section section--alt section--tight">
  <div class="wrap flex-between" style="align-items:center">
    <div style="max-width:700px">
      <h2 style="margin-bottom:6px">Looking for One Available Now?</h2>
      <p class="muted" style="margin:0">{len(USED)} used boom lifts in stock with year, origin and photos – ready for UAE delivery or export.</p>
    </div>
    <a class="btn btn--navy" href="sales-used.html">View Used Equipment</a>
  </div>
</section>

{{{{cta:Want a Machine Like These?|Tell us the model and year range you need. We source used JLG and Genie machines worldwide.}}}}
'''


# ================================================================== SOLD DETAIL (one record) – same layout as the used-sale detail page
def page_sold_detail(s):
    y, m, origin = acf(s, "year"), acf(s, "model"), acf(s, "origin")
    mtype = tax(s, "machine_type")
    tname = TYPES[mtype][1]
    sold = fmt_date(acf(s, "sold_date"))
    to = acf(s, "sold_to") or "Not recorded"
    same = [x for x in SOLD if acf(x, "model") == m]
    rent = MODEL_RENT.get(m)
    wh = MODEL_WH.get(m)

    # sale record + model specs (only specs we already hold for this model; client fills the rest)
    record = [("Make / model", m), ("Brand", m.split()[0]), ("Type", tname), ("Model year", y), ("Machine origin", origin),
              ("Sold to", to), ("Date sold", sold), ("Status", '<span class="badge badge--sold">Sold</span>')]
    rec_rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in record)
    if rent:
        rwh, rph, rout, rcap, rwt, rpw = (acf(rent, k) for k in ("working_height", "platform_height", "outreach", "capacity", "weight", "power"))
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
    avail = sorted((x for x in USED if tax(x, "machine_type") == mtype), key=lambda x: (acf(x, "model") != m, -acf(x, "year")))[:3]
    if len(avail) < 3:
        avail += sorted((x for x in USED if tax(x, "machine_type") != mtype), key=lambda x: -acf(x, "year"))[:3 - len(avail)]
    others = sorted((x for x in same if x is not s), key=lambda x: acf(x, "sold_date") or "0000", reverse=True)[:3]
    others_html = "" if not others else f'''
<section class="section section--alt section--tight">
  <div class="wrap">
    <div class="flex-between section-head" style="max-width:none"><h2 class="mt-0">Other {m} Machines We Have Sold</h2><a class="link-arrow" href="sales-sold.html">All {N_SOLD} sold records →</a></div>
    <div class="grid grid-3">
      {"".join(machine_card(x) for x in others)}
    </div>
  </div>
</section>'''
    where = f" and exported to {acf(s, 'sold_to')}" if acf(s, "sold_to") else ""
    when = f" in {sold}" if acf(s, "sold_date") else ""
    rent_link = (f'<p class="mt-24"><a class="link-arrow" href="{machine_href(rent)}">Need a {m} for a short job? Rent one from our fleet →</a></p>'
                 if rent else "")
    return f'''<section>
  <div class="wrap">
    <!-- SOLD BANNER: the page stays live after the sale (keeps its search traffic) and points buyers to similar machines -->
    <div class="sold-banner">
      <span><strong>This machine has been sold.</strong> Looking for a {m}? See machines available now, or ask us to source one.</span>
      <a class="btn btn--red btn--sm" href="sales-used.html?m_type={mtype}">See available machines</a>
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
        <a class="btn btn--red btn--block" href="contact.html#enquiry" {quote_attrs("sale", m, sold=True)}>Find Me a Similar Machine</a>
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
      <form data-quote-form="inline" novalidate>
        <input type="hidden" name="enquiry_type" value="sale"><input type="hidden" name="machine" value="{esc(m)}">
        <div class="form-grid" style="grid-template-columns:1fr">
          {lite_contact_fields("qs-", "Phone / WhatsApp")}
          <div class="field"><label for="qs-years">Year range</label><input id="qs-years" name="year_range" placeholder="e.g. {y - 2} – {y + 3}"></div>
          <div class="field"><label for="qs-country">Country</label><input id="qs-country" name="country" autocomplete="country-name" placeholder="UAE or export country"></div>
          {lite_foot("qs-", "Send request")}
        </div>
      </form>
    </aside>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="flex-between section-head" style="max-width:none"><h2 class="mt-0">Similar Machines Available Now</h2><a class="link-arrow" href="sales-used.html">All used equipment →</a></div>
    <div class="grid grid-3">
      {"".join(machine_card(x) for x in avail)}
    </div>
  </div>
</section>
{others_html}

{{{{cta:Want a {m} Like This One?|Tell us the year range and where it needs to go. We source used JLG and Genie machines worldwide.}}}}
'''


# ------------------------------------------------------------------ single-machine.php (rental / used)
# One reusable template per listing status, rendered for EVERY machine at its permalink (machine_path):
#   rental -> rental/<slug>/   used -> sales/used/<slug>/   (sold -> sales/sold/<slug>/ : page_sold_detail above)
# Everything comes from machines.json; text in [brackets] is for the content team to fill per machine.

# Extra photos per machine (WordPress: an ACF gallery field). Machines not listed show their main photo + grey slots.
GALLERY = {
    "used:2010-jlg-600aj": [("s-600aj-1", "side view"), ("s-600aj-2", "rear view"), ("s-600aj-3", "boom"),
                            ("s-600aj-4", "platform"), ("s-600aj-hours", "hour meter")],
}


def _photo(name):
    """Full-size photo when we have one, else the -sm file."""
    return name if (IMG / f"{name}.webp").exists() else name + "-sm"


def detail_gallery(photos, main_alt, scissor=False, fit="", slots=5):
    """Gallery for a detail page. photos = [(image name, thumb alt)]; the first is the main photo (LCP, eager).
    Empty slots up to `slots` are grey placeholders (photos still needed)."""
    ph = " ph--scissor" if scissor else ""
    if photos:
        main = media(_photo(photos[0][0]), main_alt, "gallery-main" + fit, True)
    else:
        main = f'<div class="ph gallery-main ph--req{ph}" data-label="Photos on request"></div>'
    thumbs = []
    for i, (name, alt) in enumerate(photos):
        act = ' class="active"' if i == 0 else ""
        thumbs.append(f'<button{act} data-src="assets/img/{_photo(name)}.webp">{media(name + "-sm", alt)}</button>')
    thumbs += [f'<button><div class="ph{ph}" data-label="Photo {n}"></div></button>' for n in range(len(photos) + 1, slots + 1)]
    return f'''{main}
      <div class="gallery-thumbs">
        {(chr(10) + "        ").join(thumbs)}
      </div>'''


def _an(word):
    """'a' / 'an' before a word or a number as it is read aloud (an 11.75 m, an 8 m, a 15.7 m)."""
    w = str(word).lower()
    return "an" if w[0] in "aeiou8" or (w[:2] in ("11", "18") and not w[:3].isdigit()) else "a"


def _rows(rows):
    return "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)


def _faq(qas):
    return "".join(f'<details{" open" if i == 0 else ""}><summary><h3>{q}</h3></summary><div><p>{a}</p></div></details>'
                   for i, (q, a) in enumerate(qas))


def page_rental_detail(it):
    c = SLUG_CAT[tax(it, "machine_type")]
    g = c["group"]
    m = acf(it, "model")
    short = m.split(" ", 1)[1]          # 'Genie GS-3246' -> 'GS-3246'
    one = c["one"]
    wh, ph, out, cap, wt, pw = (acf(it, k) for k in ("working_height", "platform_height", "outreach", "capacity", "weight", "power"))
    scissor = g["slug"] == "scissor-lifts"
    img = acf(it, "image")
    fit = " contain" if img in CONTAIN else ""
    photos = GALLERY.get(f"rental:{it['slug']}") or [(img, f"{m} front view"), (c["img"], f"{one.capitalize()} on site")]
    cat_q = one.capitalize()

    mid = (f"<div><strong>{ph:g} m</strong>Platform height</div>" if ph else f"<div><strong>{out:g} m</strong>Horizontal outreach</div>")
    if pw == "Electric":
        power_txt = "It runs on batteries – quiet and with no exhaust – so it suits indoor work and enclosed sites such as warehouses, malls, hotels and factories."
    else:
        power_txt = "It is diesel-powered for outdoor sites, construction work and uneven ground."
    reach_txt = f" It reaches {out:g} m out horizontally, so you can work over obstacles from one position." if out else ""
    spec = [("Working height", f"{wh:g} m")]
    if ph:
        spec.append(("Platform height", f"{ph:g} m"))
    if out:
        spec.append(("Horizontal outreach", f"{out:g} m"))
    spec += [("Safe working load", f"{cap} kg"), ("Machine weight", f"{wt:,} kg"),
             ("Platform size", "[from spec sheet]"),
             ("Stowed width", f"{acf(it, 'width'):g} m" if acf(it, "width") else "[from spec sheet]"),
             ("Power", "Electric (battery)" if pw == "Electric" else pw), ("Indoor / outdoor", "[from spec sheet]")]
    where = "platform" if scissor else "basket"
    faq = [(f"How many people can work on the {short} {where}?",
            f"[Your answer – based on the {cap} kg safe working load and the manufacturer's rating.]")]
    if scissor:
        faq.append((f"Can the {short} fit through a standard door?", "[Your answer – add the stowed width from the spec sheet.]"))
    else:
        faq.append((f"How far can the {short} reach?",
                    f"Up to {wh:g} m working height and {out:g} m horizontal outreach. [Add: ground conditions and set-up space it needs.]"))

    # similar: same sub-category (closest working height first), then the rest of the main category
    pool = [x for x in RENTAL_ITEMS if x is not it]
    near = lambda x: abs(acf(x, "working_height") - wh)
    similar = sorted((x for x in pool if SLUG_CAT[tax(x, "machine_type")] is c), key=near)[:3]
    if len(similar) < 3:
        similar += sorted((x for x in pool if x not in similar and SLUG_CAT[tax(x, "machine_type")]["group"] is g), key=near)[:3 - len(similar)]

    return f'''<!-- 1. TOP AREA: everything to decide in one view. First photo = LCP (no lazy). -->
<section>
  <div class="wrap detail-top">
    <div class="gallery">
      {detail_gallery(photos, f"{m} {one.lower()} for rent in Dubai", scissor, fit)}
      <p class="small muted" style="margin-top:8px">Add 4–6 real photos per machine: front, side, platform raised, controls, on site.</p>
    </div>
    <div class="detail-info">
      {STATUS[acf(it, "availability")]}
      <h1>{m} {one} for Rent</h1>
      <p class="sub">{one} · Dubai &amp; all UAE emirates</p>
      <div class="key-specs">
        <div><strong>{wh:g} m</strong>Working height</div>
        {mid}
        <div><strong>{cap} kg</strong>Safe working load</div>
        <div><strong>{pw}</strong>Power</div>
      </div>
      <div class="detail-actions">
        <a class="btn btn--red btn--block" href="contact.html#enquiry" {quote_attrs("rental", m, cat_q)}>Get a Quote for This Machine</a>
        <div class="row">
          <a class="btn btn--wa" href="{{{{WA_LINK}}}}" style="justify-content:center">{icon("wa")} WhatsApp</a>
          <a class="btn btn--navy" href="{{{{PHONE_LINK}}}}" style="justify-content:center">{icon("phone")} Call</a>
        </div>
      </div>
      <div class="assure">
        <ul>
          <li>Daily, weekly, monthly or long-term hire</li>
          <li>Delivery across all seven emirates</li>
          <li>Operator on request</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section section--alt" style="padding-top:56px">
  <div class="wrap two-col two-col--quote">
    <div class="content">
      <!-- 2. ABOUT THIS MACHINE: your own words, 80–150 words -->
      <h2>About the {m}</h2>
      <p>The {m} is {_an(one)} {one.lower()} with {_an(f"{wh:g}")} {wh:g} m working height and a {cap} kg safe working load. {power_txt}{reach_txt} [Add 2–3 lines in your own words: typical jobs your customers use it for in the UAE.]</p>

      <!-- 3. FULL SPECIFICATIONS -->
      <h2>Full Specifications</h2>
      <div class="table-wrap">
        <table class="spec-table">
          <tbody>{_rows(spec)}</tbody>
        </table>
      </div>
      <p class="mt-24"><a class="link-arrow" href="#">{icon("file")} Download manufacturer spec sheet (PDF)</a></p>

      <!-- 4. RENTAL TERMS -->
      <h2>Rental Terms</h2>
      <ul class="tick-list">
        <li>Hire periods: daily, weekly, monthly and long-term</li>
        <li>Delivery and collection across all seven emirates</li>
        <li>Machine inspected before delivery</li>
        <li>Operator available on request</li>
        <li>[What's included – e.g. charger, harness]</li>
      </ul>

      <!-- 5. QUESTIONS -->
      <h2>Questions About the {short}</h2>
      <div class="faq">
        {_faq(faq)}
      </div>
    </div>
    <!-- Sticky quote form on desktop (1024px+). Below that it is hidden: the Get a Quote button opens the popup
         and the shared enquiry section at the bottom of the page is the inline form. -->
    <aside class="side-box side-box--quote" aria-labelledby="qs-heading">
      <h3 id="qs-heading">Rent the {short}</h3>
      <p class="small muted">Tell us your site location and dates.</p>
      <form class="qf" data-quote-form="inline" novalidate>{quote_inline("qs-", "rental", m, cat_q, False)}</form>
    </aside>
  </div>
</section>

<!-- 6. SIMILAR MACHINES -->
<section class="section">
  <div class="wrap">
    <div class="flex-between section-head" style="max-width:none"><h2 class="mt-0">Similar Machines</h2><a class="link-arrow" href="{c["file"]}">All {c["name"].lower()} →</a></div>
    <div class="grid grid-3">
      {"".join(machine_card(x) for x in similar)}
    </div>
  </div>
</section>
'''


def page_used_detail(it):
    y, m, origin = acf(it, "year"), acf(it, "model"), acf(it, "origin")
    mtype = tax(it, "machine_type")
    tname = TYPES[mtype][1]
    name = f"{y} {m}"
    wh, hours, stock = acf(it, "working_height"), acf(it, "hours"), acf(it, "stock_no")
    img = acf(it, "image")
    photos = GALLERY.get(f"used:{it['slug']}") or ([(img, f"{m} side view")] if img else [])
    photos = [(n, a if a.startswith(m) else f"{m} {a}") for n, a in photos]
    rent = MODEL_RENT.get(m)

    spec = [("Make / model", m), ("Type", tname.capitalize()), ("Year", y), ("Machine origin", origin)]
    if rent:
        rout, rcap, rwt = acf(rent, "outreach"), acf(rent, "capacity"), acf(rent, "weight")
        spec += [("Working height", f"{acf(rent, 'working_height'):.2f} m")]
        if rout:
            spec.append(("Horizontal outreach", f"{rout:.2f} m"))
        spec += [("Safe working load", f"{rcap} kg"), ("Machine weight", f"{rwt:,} kg")]
        spec_src = f"Model specs from our rental fleet data for the {m}."
    else:
        spec += [("Working height", f"{wh:g} m"), ("Horizontal outreach", "[from spec sheet]"),
                 ("Safe working load", "[from spec sheet]"), ("Machine weight", "[from spec sheet]")]
        spec_src = "Working height from our sales stock data. [Add the other specs from the manufacturer spec sheet.]"
    spec.append(("Hours", hours or "[confirm]"))

    if photos:
        vid = photos[2] if len(photos) > 2 else photos[0]
        video = media(_photo(vid[0]), f"Walk-around video of the {m}", "ratio-16-9")
    else:
        video = '<div class="ph ratio-16-9 ph--req" data-label="Walk-around video"></div>'

    # similar: other used stock of the same type (same model first, then closest year), then other types
    pool = [x for x in USED if x is not it]
    key = lambda x: (acf(x, "model") != m, abs(acf(x, "year") - y))
    similar = sorted((x for x in pool if tax(x, "machine_type") == mtype), key=key)[:3]
    if len(similar) < 3:
        similar += sorted((x for x in pool if tax(x, "machine_type") != mtype), key=key)[:3 - len(similar)]

    return f'''<section>
  <div class="wrap">
    <!-- SOLD BANNER: show only when the machine is sold. Keep the page live. -->
    <div class="sold-banner">
      <span><strong>Mockup note:</strong> when this machine is sold, this banner shows: “This machine is sold – see similar machines below.”</span>
      <a class="btn btn--red btn--sm" href="sales-used.html?m_type={mtype}">See similar machines</a>
    </div>
  </div>
  <div class="wrap detail-top">
    <div class="gallery">
      {detail_gallery(photos, f"Used {name} {tname.lower()} for sale")}
    </div>
    <div class="detail-info">
      <span class="badge badge--ok">Available</span>
      <h1>Used {name} {tname} for Sale</h1>
      <p class="stock-no">Stock no. <strong>{stock or "[stock no.]"}</strong> · Machine origin: {origin}</p>
      <div class="key-specs">
        <div><strong>{y}</strong>Year</div>
        <div><strong>{origin}</strong>Origin</div>
        <div><strong>{wh:g} m</strong>Working height</div>
        <div><strong>{hours or "[hours]"}</strong>Hours</div>
      </div>
      <div class="price" style="font-size:1.6rem;margin-bottom:16px">Contact for price <small>UAE and export enquiries welcome</small></div>
      <div class="detail-actions">
        <a class="btn btn--red btn--block" href="contact.html#enquiry" {quote_attrs("sale", name)}>Enquire About This Machine</a>
        <div class="row">
          <a class="btn btn--wa" href="{{{{WA_LINK}}}}" style="justify-content:center">{icon("wa")} WhatsApp</a>
          <a class="btn btn--navy" href="{{{{PHONE_LINK}}}}" style="justify-content:center">{icon("phone")} Call</a>
        </div>
      </div>
      <p class="small muted" style="margin-top:12px">WhatsApp message is pre-filled with the machine name and page link.</p>
    </div>
  </div>
</section>

<section class="section section--alt" style="padding-top:56px">
  <div class="wrap two-col two-col--quote">
    <div class="content">
      <h2>Condition &amp; History</h2>
      <ul class="tick-list">
        <li>[Overall condition – e.g. good working order]</li>
        <li>{f"{hours} hours – [confirm from the hour-meter photo]" if hours else "[Hours – confirm from the hour-meter photo]"}</li>
        <li>[Service history / last service date]</li>
        <li>[Tyres, paint, platform condition]</li>
      </ul>
      <!-- Walk-around video: "lite" embed – the YouTube player loads only on click -->
      <div class="video-poster">
        {video}
        <div class="play"><span>▶</span></div>
      </div>
      <p class="small muted">Walk-around video – loads only when clicked.</p>

      <h2>Full Specifications</h2>
      <div class="table-wrap">
        <table class="spec-table">
          <tbody>{_rows(spec)}</tbody>
        </table>
      </div>
      <p class="small muted">{spec_src}</p>

      <h2>Shipping &amp; Export</h2>
      <p>[Only if offered: export documents, help with shipping, loading at your Dubai yard, countries you have exported to.]</p>
    </div>
    <!-- Sticky quote form on desktop (1024px+); hidden below that (popup + bottom enquiry section instead). -->
    <aside class="side-box side-box--quote" aria-labelledby="qs-heading">
      <h3 id="qs-heading">Interested in this machine?</h3>
      <p class="small muted">{name} · {origin}</p>
      <form class="qf" data-quote-form="inline" novalidate>{quote_inline("qs-", "sale", name, "", False)}</form>
    </aside>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="flex-between section-head" style="max-width:none"><h2 class="mt-0">Similar Machines for Sale</h2><a class="link-arrow" href="sales-used.html">All used equipment →</a></div>
    <div class="grid grid-3">
      {"".join(machine_card(x) for x in similar)}
    </div>
  </div>
</section>
'''


# ------------------------------------------------------------------ header / footer
def header(active):
    # Same menu as the home page header: menu_html() (styles in assets/css/menu.css, shared by both headers)
    return f'''<div class="mock-note">UI mockup for review · real photos and data from your website · grey boxes = photos still needed</div>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="index.html">
      <img src="assets/img/logo.webp" alt="Cherry Pickers Equipment – The Right Pick for Every Height" width="1024" height="340" class="logo-img">
    </a>
    {menu_html(active)}
    <div class="header-actions">
      <a class="header-phone" href="{PHONE_LINK}" aria-label="Call {PHONE}">{icon("phone")}<span>{PHONE}</span></a>
      <a class="icon-btn" href="{WA_LINK}" aria-label="WhatsApp us" target="_blank" rel="noopener">{WA_SVG}</a>
      <a class="btn btn--red btn--sm" href="contact.html#enquiry" {quote_attrs()}>Get a Quote</a>
    </div>
    <button class="menu-toggle" type="button" data-menu-open aria-label="Open menu" aria-expanded="false" aria-controls="cpe-menu"><span></span></button>
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
    cat_links = "".join(f'<li><a href="{g["file"]}">{g["name"]}{" (coming soon)" if g.get("soon") else ""}</a></li>' for g in GROUPS.values())
    cat_links += '<li><a href="rental-all.html">All rental machines</a></li>'
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
  <a class="quote" href="contact.html#enquiry" {quote_attrs()}>{icon("quote")}Get a Quote</a>
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
TICK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'


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


def jsonld(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"


def faq_jsonld(items):
    """FAQPage structured data – the same Q&As as the visible accordion (answers as plain text)."""
    return jsonld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in items]})


def home_faq_jsonld():
    return faq_jsonld(HOME_FAQ)


def breadcrumb_jsonld(crumbs, path):
    """BreadcrumbList for the visible breadcrumbs: Home + crumbs. Flat partial names resolve through LINKS; the last item is this page."""
    items = [("Home", SITE)]
    for n, u in crumbs:
        items.append((n, SITE + (LINKS[u] if u else path.replace("index.html", ""))))
    return jsonld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(items, 1)]})


def home_rcard(key):
    """Home 'Fast-moving rental machines' card. Title + Details -> the machine's own page. key = 'rental:<slug>'."""
    it = BY_KEY[key]
    m, img, ph, out, cap, wh, pw = (acf(it, k) for k in ("model", "image", "platform_height", "outreach", "capacity", "working_height", "power"))
    k = it["id"]
    c = SLUG_CAT[tax(it, "machine_type")]
    mid = (f"<div><strong>{ph:g} m</strong><span>Platform ht.</span></div>" if ph
           else f"<div><strong>{out:g} m</strong><span>Outreach</span></div>")
    pill = '<span class="pill avail">Available</span>' if acf(it, "availability") == "available" else '<span class="pill busy">On hire – ask for date</span>'
    return f'''<article class="mc">
        <div class="mc-img">{img_tag(img + "-sm", f"{m} for rent in Dubai")}{pill}</div>
        <div class="mc-body">
          <h3><a href="machine-{k}.html">{m}</a></h3>
          <div class="type">{c['one']} · {pw}</div>
          <div class="specs"><div><strong>{wh:g} m</strong><span>Working ht.</span></div>{mid}<div><strong>{cap} kg</strong><span>Capacity</span></div></div>
          <div class="mc-btns">
            <a class="btn btn-out btn-sm" href="machine-{k}.html">Details</a>
            <a class="btn btn-red btn-sm" href="#enquiry" {quote_attrs("rental", m, c["one"].capitalize())}>Get a Quote</a>
            <a class="btn btn-wa btn-icon" href="{wa_url(f"Hi, I need a quote for the {m}.")}" target="_blank" rel="noopener" aria-label="WhatsApp about {m}">{WA_SVG}</a>
          </div>
        </div>
      </article>'''


def home_scard(key):
    """Home 'High-demand used equipment' card. Photo + title -> the machine's own page under sales/used/. key = 'used:<slug>'."""
    it = BY_KEY[key]
    y, m, origin, wh, img = (acf(it, k) for k in ("year", "model", "origin", "working_height", "image"))
    tname = TYPES[tax(it, "machine_type")][1]
    href = machine_href(it)
    hours = acf(it, "hours") or "On request"
    todo = f"<!-- TODO: sample hours ({hours}) – replace with the real hour-meter reading -->" if it.get("_comment_hours") else ""
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
            <a class="btn btn-navy btn-sm" href="#enquiry" {quote_attrs("sale", f"{y} {m}")}>Enquire to Buy</a>
            <a class="btn btn-wa btn-icon" href="{wa_url(f"Hi, I'm interested in buying the used {y} {m}.")}" target="_blank" rel="noopener" aria-label="WhatsApp about the {y} {m}">{WA_SVG}</a>
          </div>
        </div>
      </article>'''


def home_cat(c):
    """Home fleet grid tile for a rental sub-category ({{homecat:<CATS key>}})."""
    return (f'<a class="cat" href="{c["file"]}"><div class="cat-img">{img_tag(c["img"] + "-sm", c["one"] + " rental in Dubai")}</div>'
            f'<div class="cat-body"><h3>{c["name"]}</h3><span class="badge-h">{c["range"]}</span><p>{c["short"]}</p></div></a>')


def group_card(g):
    """About page card for a rental main category ({{groupcard:<GROUPS key>}})."""
    meta = f"Coming soon · {g['range']}" if g.get("soon") else f"{g['n']} models · {g['range']}"
    return (f'<a class="cat-card" href="{g["file"]}">{media(g["img"] + "-sm", g["one"])}'
            f'<div class="cat-card-body"><h3>{g["name"]}</h3><span class="height">{meta}</span></div></a>')


# ------------------------------------------------------------------ main menu (shared by both headers)
# One <nav class="cpe-menu"> for desktop and mobile. Every link is in the HTML on page load; CSS (assets/css/menu.css)
# hides closed panels, and main.js only toggles classes / aria-expanded.
#   Desktop (>960px): cascading dropdowns – Rental › Boom Lifts › Telescopic … (hover intent, keyboard, flips left near the edge)
#   Mobile (<=960px): the same nav is an off-canvas drawer with drill-down panels and a Back button
# WordPress: wp_nav_menu() with a custom walker that prints this markup (menu items: Rental > Boom Lifts > Telescopic …).
def nav_tree():
    rental = []
    for g in GROUPS.values():
        note = f"{g['range']} · Coming soon" if g.get("soon") else g["range"]
        rental.append(dict(name=g["name"], url=g["file"], note=note, overview=f"View all {g['name']} →",
                           children=[dict(name=c["menu"], url=c["file"], note=c["range"]) for c in g["cats"]]))
    return [
        dict(name="Rental", url="rental.html", overview="Rental overview →", children=rental,
             foot=("All rental machines →", "rental-all.html")),
        dict(name="Sales", url="sales.html", overview="Sales overview →", children=[
            dict(name="Used Equipment", url="sales-used.html"), dict(name="New Equipment", url="sales-new.html"),
            dict(name="Sold Equipment", url="sales-sold.html")]),
        dict(name="Services", url="services.html", overview="All services →", children=[
            dict(name="AMC", url="services-amc.html", note="Annual maintenance contracts"),
            dict(name="On-site Repairs", url="services-on-site-repairs.html", note="Breakdown repair at your site"),
            dict(name="Workshop Services", url="services-workshop.html", note="Servicing &amp; overhaul in our workshop")]),
        dict(name="About", url="about.html"),
        dict(name="Blog", url="blog.html"),
        dict(name="Contact", url="contact.html"),
    ]


CHEV = '<svg class="cm-chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CHEV_BACK = '<svg class="cm-chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3L5 8l5 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def menu_items(items, level, parent=None, active=""):
    out = []
    for it in items:
        name, url = it["name"], it["url"]
        note = f'<small>{it["note"]}</small>' if it.get("note") else ""
        cur = ' aria-current="page"' if level == 1 and name.lower() == active else ""
        link = f'<a class="cm-link" href="{url}"{cur}><span>{name}</span>{note}</a>'
        if not it.get("children"):
            out.append(f'<li class="cm-item">{link}</li>')
            continue
        sid = f"cm-{slug(name)}"
        back = "Back" if level == 1 else f"Back to {parent}"
        rows = [f'<li class="cm-item cm-overview"><a class="cm-link" href="{url}">{it["overview"]}</a></li>']
        rows += menu_items(it["children"], level + 1, name)
        if it.get("foot"):
            rows.append(f'<li class="cm-item cm-more"><a class="cm-link" href="{it["foot"][1]}">{it["foot"][0]}</a></li>')
        out.append(
            f'<li class="cm-item cm-has-sub">{link}'
            f'<button class="cm-toggle" type="button" aria-expanded="false" aria-controls="{sid}" aria-label="{name} menu">'
            f'<span class="cm-tlabel"><span>{name}</span>{note}</span>{CHEV}</button>'
            f'<div class="cm-sub" id="{sid}"><div class="cm-head"><button class="cm-back" type="button">{CHEV_BACK}{back}</button>'
            f'<p class="cm-title">{name}</p></div><ul class="cm-list cm-l{level + 1}">{"".join(rows)}</ul></div></li>')
    return out


def menu_html(active=""):
    return f'''<nav class="cpe-menu" id="cpe-menu" aria-label="Main">
      <div class="cm-bar"><p class="cm-title">Menu</p><button class="cm-close" type="button" aria-label="Close menu">&times;</button></div>
      <div class="cm-body"><ul class="cm-list cm-l1">{"".join(menu_items(nav_tree(), 1, active=active))}</ul></div>
      <div class="cm-foot">
        <a class="cm-btn cm-btn--call" href="{PHONE_LINK}">{icon("phone")}Call</a>
        <a class="cm-btn cm-btn--wa" href="{WA_LINK}" target="_blank" rel="noopener">{WA_SVG}WhatsApp</a>
      </div>
    </nav>'''


def header_home():
    return f'''<header class="site-hdr" id="hdr">
  <div class="wrap hdr">
    <a class="logo" href="index.html" aria-label="Cherry Pickers Equipment home"><img src="assets/img/logo.webp" alt="Cherry Pickers Equipment – The Right Pick for Every Height" width="1024" height="340"></a>
    {menu_html()}
    <div class="hdr-cta">
      <a class="hdr-phone" href="{PHONE_LINK}" aria-label="Call {PHONE}">{icon("phone")}<span>{PHONE}</span></a>
      <a class="btn btn-wa btn-icon" href="{WA_LINK}" target="_blank" rel="noopener" aria-label="WhatsApp us">{WA_SVG}</a>
      <a class="btn btn-red btn-sm" href="#enquiry" {quote_attrs()}>Get a Quote</a>
      <button class="burger" id="burger" type="button" data-menu-open aria-label="Open menu" aria-expanded="false" aria-controls="cpe-menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
    </div>
  </div>
</header>'''


def footer_home():
    rent = "".join(f'<li><a href="{g["file"]}">{g["name"]}{" (coming soon)" if g.get("soon") else ""}</a></li>' for g in GROUPS.values())
    rent += '<li><a href="rental-all.html">All rental machines</a></li><li><a href="rental.html">Rental overview</a></li>'
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
  <a class="q" href="#enquiry" {quote_attrs()}>{icon("quote")}Get a Quote</a>
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
<link rel="stylesheet" href="assets/css/quote-modal.css">
<link rel="stylesheet" href="assets/css/menu.css">
{head_extra}{cpe_config}</head>
<body{body_class}>
{header}
<main>
{crumbs}
{body}
</main>
{footer}
{quote_modal}<script src="assets/js/main.js" defer></script>
<script src="assets/js/quote-modal.js" defer></script>
{scripts}</body>
</html>
"""


# ------------------------------------------------------------------ shared enquiry section (above the footer on every page)
# "Light touch" quote forms: each variant keeps its own fields; validation, success message and tracking come from
# assets/js/quote-modal.js (form[data-quote-form]). ids use the 'qe-' prefix (sidebar forms use 'qs-').
EMIRATES = "".join(f"<option>{e}</option>" for e in ("Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"))
CAT_OPTIONS = '<option value="">Not sure – advise me</option>' + "".join(f"<option>{c}</option>" for c in QUOTE_CATEGORIES)


def lite_contact_fields(p, phone_label="Phone / WhatsApp"):
    """Name + phone for the light-touch forms (same names, types and autocomplete as the popup)."""
    return (f'<div class="field"><label for="{p}name">Name <span class="req" aria-hidden="true">*</span></label>'
            f'<input id="{p}name" name="name" required autocomplete="name"></div>\n'
            f'          <div class="field"><label for="{p}phone">{phone_label} <span class="req" aria-hidden="true">*</span></label>'
            f'<input id="{p}phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" required placeholder="+971 50 123 4567"></div>')


def lite_foot(p, button):
    """Status line, submit button and honeypot for the light-touch forms."""
    return (f'<div class="full"><div class="qf-status" role="alert" hidden></div>'
            f'<button class="btn btn--red btn--block" type="submit">{button}</button>'
            f'<div class="qf-hp" aria-hidden="true"><label for="{p}website">Website</label>'
            f'<input id="{p}website" name="website" tabindex="-1" autocomplete="off"></div></div>')


ENQ = {
    "rental": dict(
        eyebrow="Get a quote", title="Need a Machine for Your Project?", type="rental",
        text="Tell us the working height, the job and the site location. We'll suggest the right machine and send a quote.",
        tip="WhatsApp site photos and job details",
        fields='''<div class="field"><label for="qe-category">Machine needed</label><select id="qe-category" name="machine_category">''' + CAT_OPTIONS + '''</select></div>
        <div class="field"><label for="qe-emirate">Emirate</label><select id="qe-emirate" name="emirate">''' + EMIRATES + '''</select></div>
        <div class="field full"><label for="qe-details">Job details</label><textarea id="qe-details" name="details" placeholder="Working height, type of work, site location and dates"></textarea></div>''',
        button="Send enquiry"),
    "sales": dict(
        eyebrow="Buy a machine", title="Looking for a Specific Machine?", type="sale",
        text="Tell us the model, year or working height you need. We source used boom lifts and scissor lifts worldwide.",
        tip="WhatsApp for photos and walk-around videos",
        fields='''<div class="field"><label for="qe-model">Machine or model</label><input id="qe-model" name="machine_model" placeholder="e.g. JLG 860SJ"></div>
        <div class="field"><label for="qe-country">Country</label><input id="qe-country" name="country" autocomplete="country-name" placeholder="UAE or export country"></div>
        <div class="field full"><label for="qe-details">Message</label><textarea id="qe-details" name="details" placeholder="Year range, working height, quantity or any questions"></textarea></div>''',
        button="Send enquiry"),
    "service": dict(
        eyebrow="Book a service", title="Tell Us About Your Machine", type="service",
        text="Send the brand, model and problem. Our workshop team will call you back.",
        tip="WhatsApp photos or videos of the fault",
        fields='''<div class="field"><label for="qe-smachine">Machine brand &amp; model</label><input id="qe-smachine" name="service_machine" placeholder="e.g. Genie GS-3246"></div>
        <div class="field"><label for="qe-emirate">Emirate</label><select id="qe-emirate" name="emirate">''' + EMIRATES + '''</select></div>
        <div class="field full"><label for="qe-details">Problem</label><textarea id="qe-details" name="details" placeholder="What's wrong with the machine?"></textarea></div>''',
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
    <form class="form-card" data-quote-form="inline" novalidate>
      <input type="hidden" name="enquiry_type" value="{e["type"]}">
      <div class="form-grid">
        {lite_contact_fields("qe-")}
        {e["fields"]}
        {lite_foot("qe-", e["button"])}
      </div>
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
    # machine cards by 'listing_status:slug', e.g. {{card:rental:genie-gs-2646}} / {{card:used:2018-jlg-e450aj}}
    html = re.sub(r"\{\{card:([\w:-]+)\}\}", lambda m: machine_card(BY_KEY[m.group(1)]), html)
    # home page tokens
    html = re.sub(r"\{\{hrcard:([\w:-]+)\}\}", lambda m: home_rcard(m.group(1)), html)
    html = re.sub(r"\{\{hscard:([\w:-]+)\}\}", lambda m: home_scard(m.group(1)), html)
    # rental category cards from CATS / GROUPS, e.g. {{homecat:se}} (home fleet grid) / {{groupcard:boom}} (About page)
    html = re.sub(r"\{\{homecat:(\w+)\}\}", lambda m: home_cat(CATS[m.group(1)]), html)
    html = re.sub(r"\{\{groupcard:(\w+)\}\}", lambda m: group_card(GROUPS[m.group(1)]), html)
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

    # {{quotefields:prefix|type|machine|category|flags}} -> shared quote fields (quote.py); flags: notoggle, sold
    def _qf(m):
        p = (m.group(1).split("|") + [""] * 5)[:5]
        return quote_inline(p[0], p[1] or "rental", p[2], p[3], "notoggle" not in p[4], "sold" in p[4])
    html = re.sub(r"\{\{quotefields:([^}]*)\}\}", _qf, html)

    # {{quote}} / {{quote:type|machine|category}} -> quote trigger attributes (quote.py)
    def _qa(m):
        p = ((m.group(1) or "").split("|") + [""] * 3)[:3]
        return quote_attrs(p[0], p[1], p[2])
    html = re.sub(r"\{\{quote(?::([^}]*))?\}\}", _qa, html)

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
    html = re.sub(r'(href)="([a-z0-9\-]+\.html)([?#][^"]*)?"', _href, html)
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
    ("rental/all-machines/index.html", f"All Rental Machines – {N_RENTAL} Scissor Lifts & Boom Lifts | Cherry Pickers Equipment",
     f"Browse all {N_RENTAL} scissor lift and boom lift models for rent in Dubai and the UAE. Filter by machine type, working height and brand.",
     "rental", [("Rental", "rental.html"), ("All Machines", "")], page_rental_all),
]
# main categories (/rental/{main}/), each followed by its sub-categories (/rental/{main}/{sub}/)
for g in GROUPS.values():
    _f = dict(n=g["n"], lo=g["lo"], hi=g["hi"])
    PAGES.append((f"rental/{g['slug']}/index.html", g["title"].format(**_f), g["desc"].format(**_f),
                  "rental", [("Rental", "rental.html"), (g["name"], "")], (lambda g=g: page_rental_group(g))))
    for c in g["cats"]:
        PAGES.append((f"rental/{g['slug']}/{c['slug']}/index.html",
                      f"{c['one']} Rental in Dubai & UAE – {c['n']} Models | Cherry Pickers Equipment",
                      f"Rent {c['name'].lower()} in Dubai and across the UAE: {c['n']} models from {c['lo']} to {c['hi']} working height. Daily, weekly and monthly hire.",
                      "rental", [("Rental", "rental.html"), (g["name"], g["file"]), (c["name"], "")], (lambda c=c: page_rental_category(c))))
PAGES += [
    ("sales/index.html", "Used Boom Lifts & Scissor Lifts for Sale – UAE & Export | Cherry Pickers Equipment",
     f"Buy used JLG and Genie boom lifts and scissor lifts. {len(USED)} machines available, {N_SOLD} sold and exported. Contact for price.", "sales", [("Sales", "")], page_sales_landing),
    ("sales/new/index.html", "New Access Equipment for Sale in UAE | Cherry Pickers Equipment",
     "New boom lifts and scissor lifts for sale in the UAE. Tell us the machine you need for price and delivery time.", "sales",
     [("Sales", "sales.html"), ("New Equipment", "")], page_sales_new),
    ("sales/used/index.html", "Used Access Equipment for Sale in UAE | Cherry Pickers Equipment",
     f"{len(USED)} used boom lifts for sale with year, origin and photos. Filter by type, brand, year and working height.", "sales",
     [("Sales", "sales.html"), ("Used Equipment", "")], page_sales_used),
    ("sales/sold/index.html", f"Sold Access Equipment – {N_SOLD} Sales Records | Cherry Pickers Equipment",
     f"Records of {N_SOLD} used boom lifts and scissor lifts sold and exported by Cherry Pickers Equipment, by model, year and destination.", "sales",
     [("Sales", "sales.html"), ("Sold Equipment", "")], page_sales_sold),
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


# ------------------------------------------------------------------ machine detail pages (single-machine.php)
# One sample per template (DETAIL_SAMPLE), at its permalink from machine_path():
#   rental -> rental/<slug>/     used / sold -> sales/<year>-<brand>-<model>-<stock id>/
MACHINE_PAGES = {}   # page path -> machine
for _it in [DETAIL_SAMPLE["rental"]]:
    _c = SLUG_CAT[tax(_it, "machine_type")]
    _m, _wh, _out = acf(_it, "model"), acf(_it, "working_height"), acf(_it, "outreach")
    _reach = f", {_out:g} m outreach" if _out else ""
    PAGES.append((machine_path(_it) + "index.html", f"{_m} {_c['one']} for Rent in Dubai | Cherry Pickers Equipment",
                  f"Rent the {_m} {_c['one'].lower()} in Dubai: {_wh:g} m working height{_reach}, {acf(_it, 'capacity')} kg capacity.", "rental",
                  [("Rental", "rental.html"), (_c["group"]["name"], _c["group"]["file"]), (_c["name"], _c["file"]), (_m, "")],
                  (lambda it=_it: page_rental_detail(it))))
    MACHINE_PAGES[machine_path(_it) + "index.html"] = _it
for _it in [DETAIL_SAMPLE["used"]]:
    _t, _n = TYPES[tax(_it, "machine_type")][1], f"{acf(_it, 'year')} {acf(_it, 'model')}"
    PAGES.append((machine_path(_it) + "index.html", f"Used {_n} {_t} for Sale | Cherry Pickers Equipment",
                  f"Used {_n} {_t.lower()} for sale: {acf(_it, 'working_height'):g} m working height, machine origin {acf(_it, 'origin')}. Contact for price.", "sales",
                  [("Sales", "sales.html"), ("Used Equipment", "sales-used.html"), (_n, "")],
                  (lambda it=_it: page_used_detail(it))))
    MACHINE_PAGES[machine_path(_it) + "index.html"] = _it
for _it in [DETAIL_SAMPLE["sold"]]:
    _t, _to = TYPES[tax(_it, "machine_type")][1], acf(_it, "sold_to")
    _when = f", sold {fmt_date(acf(_it, 'sold_date'))}" if acf(_it, "sold_date") else ", sold"
    PAGES.append((machine_path(_it) + "index.html", f"Sold: {_it['title']} {_t} | Cherry Pickers Equipment",
                  f"{_it['title']} {_t.lower()} from {acf(_it, 'origin')}{_when}{' to ' + _to if _to else ''}. Looking for one like it? We source used JLG and Genie machines.", "sales",
                  [("Sales", "sales.html"), ("Sold Equipment", "sales-sold.html"), (_it["title"], "")],
                  (lambda it=_it: page_sold_detail(it))))
    MACHINE_PAGES[machine_path(_it) + "index.html"] = _it
assert len({p[0] for p in PAGES}) == len(PAGES), "duplicate page path"


# ------------------------------------------------------------------ WhatsApp pre-filled messages
# Every wa.me link on a page gets the message for that page (header icon, buttons, mobile bar, footer).
WA_HI = "Hi Cherry Pickers Equipment,"
WA_RENT = "\nWorking height:\nSite location:\nDates:"
WA_DEFAULT = f"{WA_HI} I'd like more information about your access equipment."
WA_MSG = {
    "rental/index.html": f"{WA_HI} I'd like a rental quote.\nMachine type:" + WA_RENT,
    "rental/all-machines/index.html": f"{WA_HI} I'd like a rental quote.\nMachine type:" + WA_RENT,
    "rental/spider-lifts/index.html": f"{WA_HI} I'd like to register interest in renting a spider lift (17 – 36 m)." + WA_RENT,
    "sales/index.html": f"{WA_HI} I'm interested in buying a used machine.\nModel:\nWorking height:\nCountry:",
    "sales/new/index.html": f"{WA_HI} I'm interested in buying a new machine.\nModel:\nCountry:",
    "sales/used/index.html": f"{WA_HI} I'm interested in one of your used machines for sale.\nModel:\nCountry:",
    "sales/sold/index.html": f"{WA_HI} I'm looking for a machine like the ones you have sold.\nModel:\nYear range:\nCountry:",
    "services/index.html": f"{WA_HI} I'd like to know more about your services.",
    "services/maintenance-repair/index.html": f"{WA_HI} I need service or repair for a machine.\nBrand & model:\nProblem:\nLocation:",
    "contact/index.html": f"{WA_HI} I have an enquiry.",
    "services/amc/index.html": f"{WA_HI} I'd like a quote for an annual maintenance contract (AMC).\nMachines (brand & model):\nNumber of machines:\nLocation:",
    "services/on-site-repairs/index.html": f"{WA_HI} I have a machine breakdown and need an on-site repair.\nBrand & model:\nProblem:\nLocation:",
    "services/workshop-services/index.html": f"{WA_HI} I'd like to book a workshop service.\nBrand & model:\nWork needed:",
}
for _g in GROUPS.values():
    if not _g.get("soon"):
        WA_MSG[f"rental/{_g['slug']}/index.html"] = f"{WA_HI} I'd like a quote to rent a {_g['one'].lower()}.\nType:" + WA_RENT
for _c in CATS.values():
    _m = _c['one'].lower()
    WA_MSG[f"rental/{_c['group']['slug']}/{_c['slug']}/index.html"] = f"{WA_HI} I'd like a quote to rent {'an' if _m[0] in 'aeiou' else 'a'} {_m}." + WA_RENT
for _path, _it in MACHINE_PAGES.items():
    _url, _m = SITE + _path.replace("index.html", ""), acf(_it, "model")
    _st = tax(_it, "listing_status")
    if _st == "rental":
        WA_MSG[_path] = f"{WA_HI} I'd like a quote to rent the {_m} {SLUG_CAT[tax(_it, 'machine_type')]['one'].lower()}.\nSite location:\nDates:\n{_url}"
    elif _st == "used":
        WA_MSG[_path] = (f"{WA_HI} I'm interested in the used {acf(_it, 'year')} {_m} {TYPES[tax(_it, 'machine_type')][1].lower()}. "
                         f"Please send the price and more photos.\n{_url}")
    else:
        WA_MSG[_path] = f"{WA_HI} I'm looking for a machine like the {_it['title']} you sold.\nYear range:\nCountry:\n{_url}"


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
    # rental categories moved under /rental/{main}/ and machine pages became flat /rental/{slug}/ (old URLs: redirects.csv)
    for old in OLD_RENTAL_CATS:
        shutil.rmtree(OUT / "rental" / old, ignore_errors=True)
    # sales machine pages moved from /sales/{used|sold}/{slug}/ to /sales/{year}-{brand}-{model}-{stock id}/
    for status in ("new", "used", "sold"):
        for old in (OUT / "sales" / status).glob("*/"):
            shutil.rmtree(old, ignore_errors=True)
    # machine detail pages: only the DETAIL_SAMPLE pages are built, so clear any other machine folders first
    for it in RENTAL_ITEMS:
        shutil.rmtree(OUT / "rental" / it["slug"], ignore_errors=True)
    for old in (OUT / "sales").glob("[0-9]*/"):
        shutil.rmtree(old, ignore_errors=True)
    built, sitemap = [], []
    global CPE_PAGE, PAGE_LD
    for path, title, desc, active, crumbs, body in PAGES:
        CPE_PAGE = None   # set by listing() while the body renders
        PAGE_LD = None    # set by page functions that want BreadcrumbList + FAQPage JSON-LD
        raw = body() if callable(body) else (SRC / "pages" / f"{body}.html").read_text(encoding="utf-8")
        head_extra = home_faq_jsonld() if path == "index.html" else ""
        if PAGE_LD:
            head_extra += breadcrumb_jsonld(crumbs, path) + faq_jsonld(PAGE_LD["faq"])
        # WordPress: wp_localize_script('cpe-listing', 'CPE', ...) + wp_enqueue_script('cpe-listing', 'assets/js/listing.js')
        cpe_config = f"<script>window.CPE = {json.dumps(CPE_PAGE)};</script>\n" if CPE_PAGE else ""
        scripts = '<script src="assets/js/listing.js" defer></script>\n' if CPE_PAGE else ""
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
                           head_extra=head_extra, cpe_config=cpe_config, scripts=scripts,
                           body_class=' class="home"' if home else "",
                           header=header_home() if home else header(active), crumbs=crumbs_html, body=body_html,
                           footer=footer_home() if home else footer(),
                           # quote popup on every page except Contact (its own inline form is the target there)
                           quote_modal="" if path == "contact/index.html" else quote_modal() + "\n")
        html = wa_prefill(rewrite_links(html, path), path)
        out = OUT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        built.append(path)
        if not robots:   # noindexed pages stay out of the sitemap; so do filter/search URLs (never listed here)
            sitemap.append(SITE + path.replace("index.html", ""))
    # reference copy of the popup markup (WordPress: footer.php / Elementor HTML widget)
    part = OUT / "assets" / "partials" / "quote-modal.html"
    part.parent.mkdir(parents=True, exist_ok=True)
    part.write_text(quote_modal() + "\n", encoding="utf-8")
    write_sitemap(sitemap)
    n_redirects = write_redirects()
    print(f"Built {len(built)} pages, sitemap.xml ({len(sitemap)} URLs), redirects.csv ({n_redirects} rows)")


# Mockup sitemap of the built pages (WordPress: Rank Math generates it; see WORDPRESS-MAP.md section 8).
def write_sitemap(urls):
    today = date.today().isoformat()
    body = "".join(f"  <url><loc>{html_escape(u)}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n", encoding="utf-8")


# 301 map for the rental restructure, as CSV for the Redirection plugin (Tools > Import: source,target,regex,code)
# or Rank Math > Redirections (enter / import the same source -> destination pairs as 301).
def write_redirects():
    rows = [(f"/rental/{old}/", "/" + new) for old, new in OLD_RENTAL_CATS.items()]
    for it in sorted(RENTAL_ITEMS, key=lambda it: it["slug"]):
        t = tax(it, "machine_type")
        rows.append((f"/rental/{OLD_TYPE.get(t, t)}/{it['slug']}/", "/" + machine_path(it)))
    sources = {s for s, _ in rows}
    assert not any(t in sources for _, t in rows), "redirect chain"
    assert len(sources) == len(rows), "duplicate redirect source"
    with (SRC / "redirects.csv").open("w", encoding="utf-8", newline="") as f:
        f.write("source,target,regex,code\n")
        f.writelines(f"{s},{t},0,301\n" for s, t in rows)
    return len(rows)


if __name__ == "__main__":
    build()
