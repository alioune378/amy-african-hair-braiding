#!/usr/bin/env python3
"""Static site generator for Amy African Hair Braiding & Boutique (Nov 2026 redesign).

No dependencies: `python3 build.py` reads data/*.json and src/, writes dist/.

Content rules built into the generator:
- Only styles marked confirmed: true in data/services.json are shown.
- Empty fields (hours, policies, FAQ answers, About text, reviews, boutique items) are hidden, never
  replaced with placeholder or invented text.
- Instagram/TikTok videos are shown only when they have a real cover image (poster / build-time TikTok thumbnail),
  so no empty placeholders ever appear. Nothing third-party loads until a visitor taps play.
- "noindex": true in data/site.json keeps a preview deployment out of search engines.
"""
import html, json, os, re, shutil, urllib.parse, urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


S = load("site.json")
SERVICES = load("services.json")
REELS = [r for r in load("reels.json")["reels"] if r.get("instagram_url") or r.get("mp4")]
TIKS = [t for t in load("tiktoks.json").get("videos", []) if t.get("url")]
GALLERY = load("gallery.json")
PHOTOS = [p for p in GALLERY.get("photos", []) if p.get("src")]
REVIEWS = [r for r in load("reviews.json")["reviews"] if r.get("text") and r.get("author")]
SITE_URL = (os.environ.get("SITE_URL") or S.get("site_url") or "").rstrip("/")
NOINDEX = bool(S.get("noindex"))
OFFERED = [s for s in SERVICES["services"] if s.get("confirmed")]
e = lambda s: html.escape(str(s or ""), quote=True)
A = S["address"]
ADDR_LINE = f'{A["street"]}, {A["city"]}, {A["region"]} {A["postal"]}'
TEL = "tel:" + S["phone_e164"]
PHONE2 = S.get("phone_secondary") or ""
TEL2 = "tel:" + (S.get("phone_secondary_e164") or re.sub(r"[^0-9+]", "", PHONE2))
IG = S["instagram_url"]
IG_HANDLE = S.get("instagram_handle") or ""
TT = S.get("tiktok_url") or ""
TT_HANDLE = S.get("tiktok_handle") or ""
MAPS = S["google_maps_url"]
DIRECTIONS = "https://www.google.com/maps/dir/?api=1&destination=" + urllib.parse.quote_plus(f'{S["name"]}, {ADDR_LINE}')
EST = S.get("established") or ""
OG_IMAGE = S.get("share_image") or "images/logo/og-image.jpg"
ABOUT = S.get("about") or {}
BOUTIQUE = S.get("boutique") or {}
STORE = S.get("storefront") or {}
CREDIT = S.get("developer_credit") or {}
HV = S.get("hero_video") or {}
PORTRAIT = S.get("amy_portrait") or {}
PRICING = "Pricing varies depending on braid size, length and style. Your final quote will be confirmed before your appointment."

ICONS = {
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "instagram": '<rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".6" fill="currentColor"/>',
    "tiktok": '<path d="M14 3v11.5a3.5 3.5 0 1 1-3.5-3.5"/><path d="M14 3c.4 2.6 2.2 4.4 5 4.6"/>',
    "map": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "play": '<path d="M7 4.5v15l13-7.5z" fill="currentColor" stroke="none"/>',
    "pause": '<path d="M8 5v14M16 5v14" stroke-width="2.4"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "star": '<path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z" fill="currentColor" stroke="none"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "left": '<path d="M15 5l-7 7 7 7"/>',
    "right": '<path d="M9 5l7 7-7 7"/>',
    "expand": '<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>',
}


def ic(name, cls=""):
    return (f'<svg class="ic {cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[name]}</svg>')


NAV = [("index.html", "Home"), ("services.html", "Our Services"), ("gallery.html", "Style Gallery"),
       ("about.html", "Meet Amy"), ("index.html#boutique", "Boutique")]
if REVIEWS:
    NAV.append(("reviews.html", "Reviews"))
NAV.append(("contact.html", "Contact"))


def json_ld():
    ld = {"@context": "https://schema.org", "@type": "HairSalon", "name": S["name"], "telephone": S["phone_e164"],
          "address": {"@type": "PostalAddress", "streetAddress": A["street"], "addressLocality": A["city"],
                      "addressRegion": A["region"], "postalCode": A["postal"], "addressCountry": A["country"]},
          "areaServed": ["St. Ann, MO", "St. Louis, MO"], "sameAs": [u for u in (IG, TT) if u], "hasMap": MAPS}
    if EST:
        ld["foundingDate"] = EST
    if SITE_URL:
        ld["url"] = SITE_URL + "/"
        ld["logo"] = SITE_URL + "/images/logo/amy-logo-bright-600.webp"
        ld["image"] = ([SITE_URL + "/" + STORE["fallback"]] if STORE.get("fallback") else []) + [SITE_URL + "/" + OG_IMAGE]
    if OFFERED:
        ld["makesOffer"] = [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["name"]}} for s in OFFERED]
    return json.dumps(ld, ensure_ascii=False)


def head(page, title, desc, preload=""):
    canon = og_url = ""
    if SITE_URL:
        path = "" if page == "index.html" else page
        canon = f'<link rel="canonical" href="{e(SITE_URL + "/" + path)}">'
        og_url = (f'<meta property="og:url" content="{e(SITE_URL + "/" + path)}">'
                  f'<meta property="og:image" content="{e(SITE_URL)}/{OG_IMAGE}"><meta property="og:image:width" content="1200">'
                  f'<meta property="og:image:height" content="630"><meta property="og:image:alt" content="Braids by Amy: long black and honey blonde bohemian braids">'
                  f'<meta name="twitter:image" content="{e(SITE_URL)}/{OG_IMAGE}">')
    robots = '<meta name="robots" content="noindex, nofollow">' if NOINDEX else ""
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{robots}{canon}
<meta property="og:type" content="website"><meta property="og:site_name" content="{e(S["name"])}"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">{og_url}
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="favicon.ico" sizes="any"><link rel="icon" href="images/logo/favicon-32.png" type="image/png" sizes="32x32"><link rel="icon" href="images/logo/favicon-192.png" type="image/png" sizes="192x192"><link rel="apple-touch-icon" href="images/logo/apple-touch-icon-180.png">
<link rel="preload" href="assets/fonts/dmsans.woff" as="font" type="font/woff" crossorigin>
<link rel="preload" href="assets/fonts/cormorant.woff" as="font" type="font/woff" crossorigin>{preload}
<link rel="stylesheet" href="assets/css/style.css">
<script type="application/ld+json">{json_ld()}</script>
</head>
<body data-page="{e(page)}">
<a class="skip" href="#main">Skip to content</a>
{header(page)}
<main id="main" tabindex="-1">
'''


def nav_links(page, cls=""):
    return "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if h == page else ""}>{e(t)}</a></li>' for h, t in NAV)


def header(page):
    social = (f'<a href="{e(IG)}" target="_blank" rel="noopener">{ic("instagram")}<span>Instagram</span></a>'
              + (f'<a href="{e(TT)}" target="_blank" rel="noopener">{ic("tiktok")}<span>TikTok</span></a>' if TT else ""))
    return f'''<header class="hd" data-head>
  <div class="wrap hd-row">
    <a class="brand" href="index.html" aria-label="{e(S["name"])}, home">
      <img src="images/logo/amy-logo-bright-120.webp" srcset="images/logo/amy-logo-bright-120.webp 120w, images/logo/amy-logo-bright-240.webp 240w" sizes="56px" width="120" height="151" alt="{e(S["name"])} logo">
    </a>
    <nav class="nav" aria-label="Main"><ul>{nav_links(page)}</ul></nav>
    <a class="btn btn-rose btn-sm hd-book" href="contact.html#book"><span class="hd-book-l">Book Appointment</span><span class="hd-book-s">Book</span></a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu" data-menu-open>{ic("menu")}<span class="sr">Open menu</span></button>
  </div>
</header>
<div class="menu" id="menu" role="dialog" aria-modal="true" aria-label="Menu" hidden data-menu>
  <div class="menu-panel">
    <div class="menu-top">
      <img src="images/logo/amy-logo-bright-120.webp" width="120" height="151" alt="" class="menu-logo">
      <button class="menu-close" type="button" data-menu-close>{ic("close")}<span class="sr">Close menu</span></button>
    </div>
    <nav aria-label="Main"><ul class="menu-list">{nav_links(page)}</ul></nav>
    <a class="btn btn-rose btn-block" href="contact.html#book">Book Your Appointment</a>
    <p class="menu-meta"><a href="{TEL}">{ic("phone")}{e(S["phone"])}</a></p>
    <div class="menu-social">{social}</div>
  </div>
</div>'''


def foot():
    year = date.today().year
    follow = (f'<li><a href="{e(IG)}" target="_blank" rel="noopener">Instagram</a></li>'
              + (f'<li><a href="{e(TT)}" target="_blank" rel="noopener">TikTok</a></li>' if TT else ""))
    return f'''</main>
<footer class="ft" data-foot>
  <div class="wrap ft-grid">
    <div class="ft-brand">
      <img src="images/logo/amy-logo-bright-240.webp" width="240" height="303" alt="{e(S["name"])} logo" loading="lazy" decoding="async">
      <p>African hair braiding &amp; boutique in St. Ann, Missouri.</p>
    </div>
    <div>
      <h2 class="ft-h">Visit</h2>
      <address><a href="{e(DIRECTIONS)}" target="_blank" rel="noopener">{e(A["street"])}<br>{e(A["city"])}, {e(A["region"])} {e(A["postal"])}</a></address>
      <p><a href="{TEL}">{e(S["phone"])}</a></p>
      {hours_html(short=True)}
    </div>
    <div>
      <h2 class="ft-h">Explore</h2>
      <ul class="ft-links">{"".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in NAV if h != "index.html")}</ul>
    </div>
    <div>
      <h2 class="ft-h">Booking</h2>
      <ul class="ft-links"><li><a href="contact.html#book">Request an appointment</a></li><li><a href="contact.html#booking-info">How booking works</a></li><li><a href="privacy.html">Privacy policy</a></li>{follow}</ul>
    </div>
  </div>
  <div class="wrap ft-base"><p>© {year} {e(S["name"])}</p>{credit_html()}</div>
</footer>
<a class="sticky-book" href="contact.html#book" data-mbar aria-hidden="true" tabindex="-1">{ic("calendar")}<span>Book Your Appointment</span></a>
<script src="assets/js/site.js" defer></script>
</body>
</html>
'''


def credit_html():
    name, text, url = CREDIT.get("name") or "", CREDIT.get("text") or "", CREDIT.get("url") or ""
    if not text:
        return ""
    if url and name and name in text:
        before, after = text.split(name, 1)
        inner = f'{e(before)}<a href="{e(url)}" target="_blank" rel="noopener">{e(name)}</a>{e(after)}'
    else:
        inner = e(text)
    return f'<p class="ft-credit">{inner}</p>'


def hours_html(short=False):
    if S.get("hours"):
        rows = "".join(f"<li><span>{e(d)}</span><span>{e(h)}</span></li>" for d, h in S["hours"])
        return f'<ul class="hours">{rows}</ul>'
    return '<p class="muted">Please call to confirm today’s hours.</p>'


def sec_head(kicker, title, lede="", hid="", center=False, link=""):
    return (f'<div class="sh{" center" if center else ""}"><div><p class="kicker">{e(kicker)}</p>'
            f'<h2{f" id={chr(34)}{hid}{chr(34)}" if hid else ""}>{title}</h2>{f"<p class=lede>{lede}</p>" if lede else ""}</div>{link}</div>')


def photo_srcset(p):
    if not p.get("base") or not p.get("widths"):
        return ""
    return ", ".join(f'{e(p["base"])}-{w}.webp {w}w' for w in p["widths"])


def look_link(p):
    q = urllib.parse.urlencode({"style": p.get("book_as") or "", "look": p.get("alt") or "",
                                "img": f'{p["base"]}-480.webp' if p.get("base") else p.get("src", "")})
    return f"contact.html?{q}#book"


def book_style(name):
    return f"contact.html?style={urllib.parse.quote(name)}#book"


def pic(p, sizes, cls="", eager=False):
    w, h = p.get("width") or 900, p.get("height") or 1200
    ss = photo_srcset(p)
    source = f'<source type="image/webp" srcset="{ss}" sizes="{sizes}">' if ss else ""
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    pos = f' style="object-position:{e(p["position"])}"' if p.get("position") else ""
    return (f'<picture>{source}<img class="{cls}" src="{e(p["src"])}" width="{w}" height="{h}" alt="{e(p.get("alt", ""))}" '
            f'{load} decoding="async"{pos}></picture>')


def photo_item(p, sizes="(max-width: 699px) 50vw, (max-width: 1099px) 33vw, 400px", cls="g-item"):
    big = f'{p["base"]}-{p["widths"][-1]}.webp' if photo_srcset(p) else p["src"]
    link = look_link(p) if p.get("book_as") else ""
    book = f'<a class="g-book" href="{e(link)}">Book this look {ic("arrow")}</a>' if link else ""
    return (f'<li class="{cls}" data-cat="{e(p.get("style", ""))}">'
            f'<button type="button" class="g-btn" data-lightbox="{e(big)}" data-alt="{e(p.get("alt", ""))}" data-cap="{e(p.get("style", ""))}" '
            f'data-book="{e(link)}" aria-label="View larger: {e(p.get("alt", ""))}">{pic(p, sizes)}<span class="g-zoom">{ic("expand")}</span></button>'
            f'<div class="g-meta"><span class="g-cap">{e(CAT_LABEL.get(p.get("style", ""), p.get("style", "")))}</span>{book}</div></li>')


def lightbox():
    return ('<div class="lightbox" data-lb hidden role="dialog" aria-modal="true" aria-label="Photo viewer">'
            f'<div class="lb-top"><span class="lb-count" data-lb-count></span><button type="button" class="lb-close" data-lb-close aria-label="Close">{ic("close")}</button></div>'
            '<figure class="lb-fig"><img alt="" data-lb-img><figcaption><span class="lb-cap" data-lb-cap></span>'
            f'<a class="btn btn-rose btn-sm" data-lb-book href="contact.html#book">Book this look</a></figcaption></figure>'
            f'<button type="button" class="lb-nav lb-prev" data-lb-prev aria-label="Previous photo">{ic("left")}</button>'
            f'<button type="button" class="lb-nav lb-next" data-lb-next aria-label="Next photo">{ic("right")}</button></div>')


def interleave(photos):
    """Order photos so the same style never sits next to itself when avoidable."""
    pool = list(photos)
    out = []
    while pool:
        last = out[-1].get("style") if out else None
        pick = next((p for p in pool if p.get("style") != last), pool[0])
        out.append(pick)
        pool.remove(pick)
    return out


# ---------------------------------------------------------------- shared sections
def hero():
    v = HV
    return f'''<section class="hero" aria-labelledby="hero-h">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="kicker">African Hair Braiding &amp; Boutique · St. Ann, Missouri</p>
      <h1 id="hero-h">Beautiful Braids.<br>Beautiful Confidence.</h1>
      <p class="hero-lede">Authentic African braiding, thoughtfully crafted styles and personal attention. Discover your next look with Amy.</p>
      <div class="hero-ctas">
        <a class="btn btn-rose" href="contact.html#book">Book Your Appointment</a>
        <a class="link-arrow" href="gallery.html">Explore Our Styles {ic("arrow")}</a>
      </div>
      <ul class="hero-notes"><li>{ic("map")}<span>{e(A["street"])}, St. Ann</span></li><li>{ic("calendar")}<span>Request online, no account needed</span></li></ul>
    </div>
    <figure class="hero-film" data-hero>
      <div class="hero-frame">
        <picture class="hero-poster"><source type="image/webp" srcset="{e(v.get("poster_webp"))}"><img src="{e(v.get("poster"))}" width="{v.get("width")}" height="{v.get("height")}" alt="{e(v.get("alt"))}" fetchpriority="high" decoding="async"></picture>
        <video class="hero-video" muted loop playsinline preload="none" poster="{e(v.get("poster"))}" width="{v.get("width")}" height="{v.get("height")}" aria-hidden="true" tabindex="-1" data-hero-video>
          <source data-src="{e(v.get("webm"))}" type="video/webm">
          <source data-src="{e(v.get("mp4"))}" type="video/mp4">
        </video>
        <button class="hero-toggle" type="button" hidden data-hero-toggle><span class="t-pause">{ic("pause")}</span><span class="t-play">{ic("play")}</span><span class="sr" data-hero-label>Pause video</span></button>
      </div>
      <figcaption class="hero-cap"><span class="dot" aria-hidden="true"></span>Amy at work · filmed in her St. Ann salon</figcaption>
    </figure>
  </div>
</section>'''


def services_home():
    picks = [s for s in OFFERED if s.get("image")][:6]
    cards = "".join(f'''<li class="svc">
  <a class="svc-img" href="{book_style(s["name"])}" tabindex="-1" aria-hidden="true"><img src="{e(s["image"])}" alt="" loading="lazy" decoding="async"{f' style="object-position:{e(s["image_position"])}"' if s.get("image_position") else ""}></a>
  <h3>{e(s["name"])}</h3><p>{e(s["description"])}</p>
  <a class="link-arrow sm" href="{book_style(s["name"])}">Book This Style {ic("arrow")}</a>
</li>''' for s in picks)
    return f'''<section class="sec" aria-labelledby="svc-h">
  <div class="wrap">
    {sec_head("Signature services", "Braiding, done with care", PRICING, "svc-h", link='<a class="link-arrow" href="services.html">All services ' + ic("arrow") + '</a>')}
    <ul class="svc-row">{cards}</ul>
  </div>
</section>'''


def featured_home():
    photos = [p for p in PHOTOS if p.get("home")][:5] or PHOTOS[:5]
    photos = interleave(photos)
    if not photos:
        return ""
    items = "".join(photo_item(p, "(max-width: 699px) 50vw, 33vw" if i else "(max-width: 699px) 100vw, 50vw", "g-item" + (" g-lead" if i == 0 else "")) for i, p in enumerate(photos))
    return f'''<section class="sec sec-tight" aria-labelledby="feat-h">
  <div class="wrap">
    {sec_head("The style collection", "Real styles from Amy’s chair", "Every photo is Amy’s own work. Tap any look to see it larger, then book it in one step.", "feat-h", link='<a class="link-arrow" href="gallery.html">Full gallery ' + ic("arrow") + '</a>')}
    <ul class="feature">{items}</ul>
  </div>
</section>'''


def meet_block(page_level=False):
    p = PORTRAIT
    H = "h1" if page_level else "h2"
    specialties = ", ".join(s["name"] for s in OFFERED)
    return f'''<div class="meet">
  <figure class="meet-photo"><picture><source type="image/webp" srcset="{e(p.get("src"))}"><img src="{e(p.get("fallback"))}" width="{p.get("width")}" height="{p.get("height")}" alt="{e(p.get("alt"))}" loading="lazy" decoding="async"></picture></figure>
  <div class="meet-copy">
    <p class="kicker">Meet Amy</p>
    <{H} id="meet-h">The Hands Behind Every Beautiful Braid</{H}>
    <p class="meet-lede">Meet Amy, the braider behind {e(S["name"])}. Her work brings together traditional African braiding techniques, creativity and attention to detail to help every client feel confident in her own style.</p>
    <dl class="meet-facts">
      <div><dt>The salon</dt><dd>{e(A["street"])}, St. Ann, Missouri</dd></div>
      <div><dt>Specialties</dt><dd>{e(specialties)}</dd></div>
      <div><dt>Follow her work</dt><dd><a href="{e(IG)}" target="_blank" rel="noopener">@{e(IG_HANDLE)}</a>{f' · <a href="{e(TT)}" target="_blank" rel="noopener">TikTok</a>' if TT else ""}</dd></div>
    </dl>
    {"" if page_level else f'<a class="link-arrow" href="about.html">More about Amy {ic("arrow")}</a>'}
  </div>
</div>'''


def steps_block(hid="steps-h"):
    steps = [("01", "Choose Your Style", "Browse Amy’s work and select your favorite hairstyle."),
             ("02", "Request Your Appointment", "Choose your preferred date and provide your contact details."),
             ("03", "Get Ready for Your New Look", "Receive confirmation from Amy and visit the salon for your appointment.")]
    return f'''<div class="steps">
  <h2 class="steps-h" id="{hid}">How booking works</h2>
  <ol>{"".join(f'<li><span class="n">{n}</span><div><h3>{t}</h3><p>{d}</p></div></li>' for n, t, d in steps)}</ol>
</div>'''


def boutique_block():
    if not BOUTIQUE.get("show"):
        return ""
    items = [i for i in BOUTIQUE.get("items", []) if i.get("name") and i.get("image")]
    grid = ""
    if items:
        grid = '<ul class="bq-grid">' + "".join(
            f'<li><img src="{e(i["image"])}" alt="{e(i["name"])}" loading="lazy" decoding="async"><h3>{e(i["name"])}</h3>'
            + (f"<p>{e(i['note'])}</p>" if i.get("note") else "") + "</li>" for i in items) + "</ul>"
    cats = BOUTIQUE.get("categories", []) if BOUTIQUE.get("confirmed") else []
    cat_line = f'<p class="bq-cats">{" · ".join(e(c) for c in cats)}</p>' if cats else ""
    return f'''<section class="boutique" id="boutique" aria-labelledby="bq-h">
  <div class="wrap bq-in">
    <div class="bq-mark" aria-hidden="true"><img src="images/logo/amy-logo-bright-240.webp" width="240" height="303" alt="" loading="lazy" decoding="async"></div>
    <div class="bq-copy">
      <p class="kicker">The boutique</p>
      <h2 id="bq-h">A Little Something Extra</h2>
      <p>The boutique is part of the salon visit: ask what’s in store today when you come in for your appointment, or send Amy a question ahead of time.</p>
      {cat_line}
    </div>
    <a class="btn btn-line" href="{book_style("Boutique inquiry")}">Ask About the Boutique</a>
    {grid}
  </div>
</section>'''


def has_cover(r):
    return bool(r.get("poster") or r.get("thumb") or r.get("mp4"))


def social_tile(kind, url, handle, photo):
    label = "Instagram" if kind == "instagram" else "TikTok"
    return f'''<li class="vt vt-link">
  <a href="{e(url)}" target="_blank" rel="noopener">
    {pic(photo, "(max-width: 699px) 60vw, 280px", "vt-img")}
    <span class="vt-over"><span class="vt-src">{ic(kind)}{label}</span><span class="vt-t">More of Amy’s work</span><span class="vt-h">@{e(handle)} {ic("external")}</span></span>
  </a>
</li>'''


def platform_card(kind, title, url, cover, data):
    label = "Instagram" if kind == "instagram" else "TikTok"
    return f'''<li class="vt" data-kind="{kind}" {data}>
  <div class="vt-frame">
    <button class="vt-play" type="button" data-load aria-label="Play “{e(title)}” ({label})">
      <img class="vt-img" src="{e(cover)}" alt="" loading="lazy" decoding="async"><span class="vt-pb">{ic("play")}</span>
    </button>
    <div class="vt-embed" data-embed></div>
  </div>
  <p class="vt-cap">{e(title)} <a href="{e(url)}" target="_blank" rel="noopener">{label} {ic("external")}</a></p>
</li>'''


def video_gallery(home):
    film = {"mp4": "media/salon-showcase-v1.mp4", "poster": "media/salon-showcase-poster-v1.jpg"}
    tiles = [f'''<li class="vt" data-kind="film">
  <div class="vt-frame" data-showcase>
    <video width="464" height="832" controls playsinline preload="none" poster="{film["poster"]}" aria-label="Video from Amy’s salon: finished braided styles" data-showcase-video><source src="{film["mp4"]}" type="video/mp4"></video>
    <button class="vt-play vt-cover" type="button" data-showcase-play hidden><img class="vt-img" src="{film["poster"]}" alt="" loading="lazy" decoding="async"><span class="vt-pb">{ic("play")}</span><span class="sr">Play the salon video, with sound</span></button>
  </div>
  <p class="vt-cap">Finished styles, straight from the salon <span>With sound</span></p>
</li>''']
    for r in REELS:
        if has_cover(r) and (r.get("home") or not home):
            tiles.append(platform_card("instagram", r.get("title") or "Braiding by Amy", r["instagram_url"], r.get("poster"), f'data-permalink="{e(r["instagram_url"])}"'))
    for t in TIKS:
        if has_cover(t) and (t.get("home") or not home):
            tiles.append(platform_card("tiktok", t.get("title") or "Amy on TikTok", t["url"], t.get("thumb"), f'data-url="{e(t["url"])}" data-vid="{e(t.get("video_id", ""))}"'))
    if home:
        tiles = tiles[:4]
    used = {p.get("base") for p in PHOTOS if p.get("home")}
    spare = [p for p in PHOTOS if p.get("base") not in used] or PHOTOS
    if len(spare) >= 2:
        tiles.append(social_tile("instagram", IG, IG_HANDLE, spare[0]))
        if TT:
            tiles.append(social_tile("tiktok", TT, TT_HANDLE, spare[min(3, len(spare) - 1)]))
    return f'''<section class="sec" id="videos" aria-labelledby="vid-h">
  <div class="wrap">
    {sec_head("Videos", "Fresh From Amy’s Chair", "Real clients and finished styles, filmed at the salon and shared on Amy’s Instagram and TikTok.", "vid-h")}
  </div>
  <ul class="vrail" tabindex="0" aria-label="Videos">{"".join(tiles)}</ul>
</section>'''


def visit_block():
    if not STORE.get("image_base"):
        return ""
    base, widths = STORE["image_base"], STORE.get("widths") or []
    ss = ", ".join(f"{base}-{w}.webp {w}w" for w in widths)
    second = f'<p class="muted small">Also: <a href="{TEL2}">{e(PHONE2)}</a></p>' if PHONE2 else ""
    return f'''<section class="sec visit" id="visit" aria-labelledby="visit-h">
  <div class="wrap visit-grid">
    <figure class="visit-photo"><picture><source type="image/webp" srcset="{e(ss)}" sizes="(max-width: 859px) 92vw, 520px"><img src="{e(STORE["fallback"])}" width="{STORE.get("width", 900)}" height="{STORE.get("height", 1125)}" alt="{e(STORE.get("alt") or "Salon storefront")}" loading="lazy" decoding="async"></picture></figure>
    <div class="visit-copy">
      <p class="kicker">Visit the salon</p>
      <h2 id="visit-h">Find us on St. Charles Rock Road</h2>
      <address class="visit-addr"><strong>{e(S["name"])}</strong><span>{e(A["street"])}</span><span>{e(A["city"])}, {e(A["region"])} {e(A["postal"])}</span></address>
      <ul class="visit-list">
        <li>{ic("phone")}<a href="{TEL}">{e(S["phone"])}</a></li>
        <li>{ic("clock")}<span>{"See hours below" if S.get("hours") else "Please call to confirm today’s hours."}</span></li>
      </ul>
      {hours_html() if S.get("hours") else ""}
      <div class="visit-actions">
        <a class="btn btn-rose" href="contact.html#book">Book Your Appointment</a>
        <a class="btn btn-line" href="{e(DIRECTIONS)}" target="_blank" rel="noopener">{ic("map")}<span>Get Directions</span></a>
      </div>
      {second}
    </div>
  </div>
</section>'''


def final_cta():
    return f'''<section class="final" aria-labelledby="final-h">
  <div class="wrap final-in">
    <h2 id="final-h">Your Next Beautiful Look Starts Here.</h2>
    <p>Find a style you love and let Amy bring it to life.</p>
    <div class="final-ctas"><a class="btn btn-rose" href="contact.html#book">Book Your Appointment</a><a class="btn btn-line" href="{TEL}">{ic("phone")}<span>Call the Salon</span></a></div>
  </div>
</section>'''


def review_card(r):
    stars = "".join(ic("star") for _ in range(int(r.get("rating") or 0)))
    return f'''<figure class="review">
  {f'<div class="stars" aria-label="{e(r["rating"])} out of 5 stars">{stars}</div>' if stars else ""}
  <blockquote><p>{e(r["text"])}</p></blockquote>
  <figcaption><strong>{e(r["author"])}</strong><span>{e(r.get("source", "Google"))}{f" · {e(r['date'])}" if r.get("date") else ""}</span></figcaption>
</figure>'''


def page_hero(kicker, title, lede, extra=""):
    return f'''<section class="ph">
  <div class="wrap">
    <p class="kicker">{e(kicker)}</p>
    <h1>{title}</h1>
    <p class="lede">{lede}</p>{extra}
  </div>
</section>'''


# ---------------------------------------------------------------- pages
def page_home():
    reviews = ([r for r in REVIEWS if r.get("home")][:3] or REVIEWS[:3])
    reviews_block = (f'<section class="sec"><div class="wrap">{sec_head("Client experiences", "Kind words from clients", center=True)}'
                     f'<div class="reviews">{"".join(review_card(r) for r in reviews)}</div></div></section>') if reviews else ""
    preload = f'<link rel="preload" as="image" href="{e(HV.get("poster_webp"))}" type="image/webp" fetchpriority="high">'
    return head("index.html", "Amy African Hair Braiding & Boutique | St. Ann, Missouri",
                "Discover authentic African hair braiding, box braids, feed-in braids, bohemian styles and more at Amy African Hair Braiding & Boutique in St. Ann, Missouri. Request your appointment online.",
                preload) + f'''
{hero()}
{services_home()}
{featured_home()}
<section class="sec sec-meet" aria-labelledby="meet-h"><div class="wrap">{meet_block()}</div></section>
<section class="sec sec-tight" aria-labelledby="steps-h"><div class="wrap">{steps_block()}</div></section>
{reviews_block}
{boutique_block()}
{video_gallery(home=True)}
{visit_block()}
{final_cta()}
{lightbox()}
''' + foot()


def page_services():
    with_img = [s for s in OFFERED if s.get("image")]
    no_img = [s for s in OFFERED if not s.get("image")]
    cards = "".join(f'''<article class="svc-card" id="{e(s["slug"])}">
  <a class="svc-img" href="{book_style(s["name"])}" tabindex="-1" aria-hidden="true"><img src="{e(s["image"])}" alt="" loading="lazy" decoding="async"{f' style="object-position:{e(s["image_position"])}"' if s.get("image_position") else ""}></a>
  <div><h2>{e(s["name"])}</h2><p>{e(s["description"])}</p>{f'<p class="muted small">{e(s["duration"])}</p>' if s.get("duration") else ""}{f'<p class="price">From {e(s["price_from"])}</p>' if s.get("price_from") else ""}
  <a class="btn btn-line btn-sm" href="{book_style(s["name"])}">Book This Style</a></div>
</article>''' for s in with_img)
    extra = ""
    if no_img:
        extra = '<div class="svc-extra"><h2>Also offered</h2><ul>' + "".join(
            f'<li id="{e(s["slug"])}"><div><h3>{e(s["name"])}</h3><p>{e(s["description"])}</p></div><a class="link-arrow sm" href="{book_style(s["name"])}">Book {ic("arrow")}</a></li>' for s in no_img) + "</ul></div>"
    faq = [f for f in S.get("faq", []) if f.get("a")]
    faq_html = (f'<section class="sec"><div class="wrap narrow">{sec_head("Good to know", "Questions & answers")}'
                f'<div class="faq">{"".join(f"<details><summary>{e(f[chr(113)])}</summary><p>{e(f[chr(97)])}</p></details>" for f in faq)}</div></div></section>') if faq else ""
    return head("services.html", "Braiding Services | Amy African Hair Braiding & Boutique, St. Ann, MO",
                "African braids, box braids, feed-in braids, bohemian braids, curly twists, hair extensions and styling at Amy African Hair Braiding & Boutique in St. Ann, Missouri.") + page_hero(
        "Our services", "Find your next style",
        PRICING) + f'''
<section class="sec sec-top0"><div class="wrap">
  <div class="svc-grid">{cards}</div>
  {extra}
  <p class="center"><a class="link-arrow" href="{book_style("Not sure yet")}">Not sure which style? Ask Amy {ic("arrow")}</a></p>
</div></section>
<section class="sec sec-tight"><div class="wrap">{steps_block()}</div></section>
{faq_html}
{final_cta()}
''' + foot()


CAT_ORDER = ["Box Braids", "Feed-In Braids / Cornrows", "Boho & Goddess-Inspired Braids", "Twists & Curly Styles", "Other Braiding Styles"]
CAT_LABEL = {"Boho & Goddess-Inspired Braids": "Boho & Goddess", "Feed-In Braids / Cornrows": "Feed-In & Cornrows", "Twists & Curly Styles": "Twists & Curls"}


def page_gallery():
    photos = interleave(PHOTOS)
    styles = sorted({p.get("style") for p in PHOTOS if p.get("style")}, key=lambda c: CAT_ORDER.index(c) if c in CAT_ORDER else 99)
    filt = ('<div class="filters" role="group" aria-label="Filter by style" data-filter-group="gal">'
            '<button type="button" class="chip" aria-pressed="true" data-filter="all">All Styles</button>'
            + "".join(f'<button type="button" class="chip" aria-pressed="false" data-filter="{e(c)}">{e(CAT_LABEL.get(c, c))}</button>' for c in styles)
            + "</div>") if len(styles) > 1 else ""
    return head("gallery.html", "Style Gallery | Box Braids, Feed-Ins & Boho Braids by Amy, St. Ann, MO",
                "Real hairstyles by Amy African Hair Braiding in St. Ann, Missouri: box braids, feed-in braids, boho braids and curly twists. Tap any look to book it.") + page_hero(
        "Style gallery", "Signature styles by Amy",
        "Every photo is a real client and real work from Amy’s chair. Tap a look to see it larger, then book it: your choice is carried straight into the booking form.") + f'''
<section class="sec sec-top0" id="portfolio" aria-label="Portfolio"><div class="wrap">
  {filt}
  <ul class="masonry" data-filter-target="gal">{"".join(photo_item(p) for p in photos)}</ul>
</div></section>
{video_gallery(home=False)}
{final_cta()}
{lightbox()}
''' + foot()


def page_about():
    blocks = [("Her story", "story"), ("Experience", "experience"), ("Her approach", "approach"),
              ("The salon & team", "team"), ("The boutique", "vision")]
    out = []
    for title, key in blocks:
        v = ABOUT.get(key)
        if v:
            paras = v if isinstance(v, list) else [v]
            out.append(f'<div class="about-block"><h2>{e(title)}</h2>{"".join(f"<p>{e(p)}</p>" for p in paras)}</div>')
    photos = [p for p in PHOTOS if not p.get("home")][:3]
    strip = (f'<ul class="about-strip">{"".join(photo_item(p, "(max-width: 699px) 33vw, 300px") for p in photos)}</ul>') if photos else ""
    return head("about.html", "Meet Amy | Amy African Hair Braiding & Boutique, St. Ann, MO",
                "Meet Amy, the braider behind Amy African Hair Braiding & Boutique in St. Ann, Missouri.") + f'''
<section class="sec" aria-labelledby="meet-h"><div class="wrap">{meet_block(page_level=True)}</div></section>
{f'<section class="sec sec-top0"><div class="wrap narrow">{"".join(out)}</div></section>' if out else ""}
<section class="sec sec-tight"><div class="wrap">
  {sec_head("Her work", "A few recent looks", link='<a class="link-arrow" href="gallery.html">See the gallery ' + ic("arrow") + '</a>')}
  {strip}
</div></section>
{video_gallery(home=True)}
{final_cta()}
{lightbox()}
''' + foot()


def page_reviews():
    cards = "".join(review_card(r) for r in REVIEWS)
    return head("reviews.html", "Reviews | Amy African Hair Braiding, St. Ann, MO",
                "Client reviews of Amy African Hair Braiding & Boutique in St. Ann, MO.") + page_hero(
        "Reviews", "Kind words from clients", "Read what clients say on Google, and share your own experience.",
        f'<p><a class="link-arrow" href="{e(S["google_reviews_url"])}" target="_blank" rel="noopener">Reviews on Google {ic("external")}</a></p>') + f'''
<section class="sec sec-top0"><div class="wrap"><div class="reviews">{cards}</div></div></section>
''' + foot()


def page_contact():
    opts = "".join(f'<option value="{e(s["name"])}">{e(s["name"])}</option>' for s in OFFERED)
    pol = S.get("policies", {})
    pol_items = [(t, pol.get(k)) for t, k in (("Deposits", "deposit"), ("Cancellations", "cancellation"),
                                              ("Late arrivals", "late_arrival"), ("Hair preparation", "hair_preparation"))]
    pol_html = "".join(f'<div><h3>{e(t)}</h3><p>{e(v)}</p></div>' for t, v in pol_items if v)
    pol_section = (f'<div class="policies"><h2>Booking policies</h2>{pol_html}</div>') if pol_html else ""
    second = f'<li>{ic("phone")}<a href="{TEL2}">{e(PHONE2)}</a></li>' if PHONE2 else ""
    return head("contact.html", "Book an Appointment | Amy African Hair Braiding & Boutique, St. Ann, MO",
                f"Request a braiding appointment at Amy African Hair Braiding & Boutique, {ADDR_LINE}. Choose your style and preferred date online.") + f'''
<section class="sec book-sec" id="book">
  <div class="wrap book-grid">
    <div class="book-main">
      <p class="kicker">Book your appointment</p>
      <h1>Request an appointment</h1>
      <p class="lede">Tell Amy the style and the day you’d like. It takes about a minute, and no account is needed.</p>
      <form class="book-form" name="booking" method="POST" action="booking-received.html" enctype="multipart/form-data"
            data-netlify="true" netlify-honeypot="company" data-book data-phone="{e(S["phone"])}" novalidate>
        <input type="hidden" name="form-name" value="booking">
        <input type="hidden" name="selected_look" value="" data-look-input>
        <p class="hp" aria-hidden="true"><label>Leave this empty <input name="company" tabindex="-1" autocomplete="off"></label></p>
        <div class="look" data-look hidden><img alt="" data-look-img width="64" height="96"><div><span class="kicker">Your selected look</span><p data-look-text></p></div><button type="button" class="look-x" data-look-clear aria-label="Remove selected look">{ic("close")}</button></div>
        <div class="f2">
          <div class="f"><label for="b-name">Name</label><input id="b-name" name="name" autocomplete="name" required aria-describedby="b-name-err"><p class="f-err" id="b-name-err"></p></div>
          <div class="f"><label for="b-phone">Phone number</label><input id="b-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" required pattern="[0-9+()\\-\\s.]{{7,}}" aria-describedby="b-phone-err"><p class="f-err" id="b-phone-err"></p></div>
        </div>
        <div class="f"><label for="b-email">Email <span class="opt">optional</span></label><input id="b-email" name="email" type="email" autocomplete="email" inputmode="email" aria-describedby="b-email-err"><p class="f-err" id="b-email-err"></p></div>
        <div class="f"><label for="b-style">Preferred hairstyle</label>
          <select id="b-style" name="style" required aria-describedby="b-style-err"><option value="">Choose a style…</option>{opts}<option value="Not sure yet">Not sure yet</option><option value="Boutique inquiry">Boutique question</option></select><p class="f-err" id="b-style-err"></p></div>
        <div class="f2">
          <div class="f"><label for="b-date">Preferred date</label><input id="b-date" name="date" type="date" required aria-describedby="b-date-err"><p class="f-err" id="b-date-err"></p></div>
          <div class="f"><label for="b-time">Preferred time</label>
            <select id="b-time" name="time" required aria-describedby="b-time-err"><option value="">Choose…</option><option>Morning</option><option>Midday</option><option>Afternoon</option><option>Evening</option><option>I’m flexible</option></select><p class="f-err" id="b-time-err"></p></div>
        </div>
        <details class="more-f">
          <summary>Add braid size, length or a reference photo <span class="opt">optional</span></summary>
          <div class="f2">
            <div class="f"><label for="b-size">Braid size</label><select id="b-size" name="braid_size"><option value="">Not sure</option><option>Small</option><option>Medium</option><option>Large</option></select></div>
            <div class="f"><label for="b-length">Length</label><select id="b-length" name="length"><option value="">Not sure</option><option>Shoulder</option><option>Mid-back</option><option>Waist</option><option>Past the waist</option></select></div>
          </div>
          <div class="f"><label for="b-photo">Reference photo <span class="opt">up to 8 MB</span></label>
            <input id="b-photo" name="inspiration_photo" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif"><p class="f-err" id="b-photo-err"></p></div>
        </details>
        <div class="f"><label for="b-details">Notes <span class="opt">optional</span></label><textarea id="b-details" name="details" rows="3" placeholder="Color, hair you’re bringing, anything Amy should know…"></textarea></div>
        <p class="form-msg" data-msg role="status" aria-live="polite"></p>
        <button class="btn btn-rose btn-block" type="submit" data-submit><span>Send my request</span></button>
        <p class="form-note">{ic("clock")}<span>This is a request, not a confirmed booking. Amy will contact you to confirm availability and pricing.</span></p>
        <p class="privacy">Your details are used only to arrange your appointment. <a href="privacy.html">Privacy policy</a></p>
      </form>
    </div>
    <aside class="book-side">
      {store_thumb()}
      <h2>Visit the salon</h2>
      <address><strong>{e(S["name"])}</strong><br>{e(A["street"])}<br>{e(A["city"])}, {e(A["region"])} {e(A["postal"])}</address>
      <ul class="visit-list">
        <li>{ic("phone")}<a href="{TEL}">{e(S["phone"])}</a></li>{second}
        <li>{ic("instagram")}<a href="{e(IG)}" target="_blank" rel="noopener">@{e(IG_HANDLE)}</a></li>
        {f'<li>{ic("tiktok")}<a href="{e(TT)}" target="_blank" rel="noopener">@{e(TT_HANDLE)}</a></li>' if TT else ""}
      </ul>
      <h3>Hours</h3>
      {hours_html()}
      <a class="btn btn-line btn-block" href="{e(DIRECTIONS)}" target="_blank" rel="noopener">{ic("map")}<span>Get Directions</span></a>
    </aside>
  </div>
</section>
<section class="sec sec-tight" id="booking-info"><div class="wrap">
  {steps_block("bi-h")}
  <p class="center muted pricing-note">{PRICING}</p>
  {pol_section}
</div></section>
''' + foot()


def store_thumb():
    if not STORE.get("image_base"):
        return ""
    return (f'<img class="side-store" src="{e(STORE["image_base"])}-560.webp" width="560" height="{round(560 * STORE.get("height", 1402) / STORE.get("width", 1122))}" '
            f'alt="{e(STORE.get("alt") or "Salon storefront")}" loading="lazy" decoding="async">')


def page_received():
    return head("booking-received.html", "Request received | Amy African Hair Braiding",
                "Your appointment request has been received.") + f'''
<section class="ph ph-tall">
  <div class="wrap narrow center">
    <p class="kicker">{ic("check")} Request received</p>
    <h1>Thank you.</h1>
    <p class="lede">Your appointment request has been received. Amy will contact you to confirm availability and pricing.</p>
    <p class="muted">Your appointment is not confirmed until you hear from the salon.</p>
    <div class="center-row"><a class="btn btn-rose" href="gallery.html">Keep browsing styles</a><a class="btn btn-line" href="index.html">Back to home</a></div>
  </div>
</section>
''' + foot()


def page_privacy():
    return head("privacy.html", "Privacy Policy | Amy African Hair Braiding & Boutique",
                "How Amy African Hair Braiding & Boutique handles the details you send with an appointment request.") + page_hero(
        "Privacy", "Privacy policy", "How your details are handled when you request an appointment.") + f'''
<section class="sec sec-top0"><div class="wrap narrow prose">
  <h2>What we collect</h2>
  <p>When you send an appointment request we receive the details you enter: your name, phone number, optional email address, preferred style, date and time, optional braid size, length, notes and an optional reference photo.</p>
  <h2>How it is used</h2>
  <p>These details are used only to contact you about your appointment. They are not sold, shared or used for marketing.</p>
  <h2>Where it is stored</h2>
  <p>Requests are delivered through the website’s hosting provider (Netlify Forms) and stored privately so the salon can respond.</p>
  <h2>Questions or removal</h2>
  <p>To ask about or remove your details, call the salon at <a href="{TEL}">{e(S["phone"])}</a>.</p>
  <h2>Videos from Instagram and TikTok</h2>
  <p>Instagram and TikTok videos load only when you tap play. Those platforms then apply their own privacy policies.</p>
</div></section>
''' + foot()


def page_404():
    return head("404.html", "Page not found | Amy African Hair Braiding", "This page could not be found.") + f'''
<section class="ph ph-tall"><div class="wrap narrow center">
  <h1>Page not found</h1>
  <p class="lede">The page you’re looking for has moved.</p>
  <div class="center-row"><a class="btn btn-rose" href="contact.html#book">Book appointment</a><a class="btn btn-line" href="index.html">Home</a></div>
</div></section>
''' + foot()


# ---------------------------------------------------------------- build
def resolve_tiktoks():
    """At build time (Netlify has internet), fetch each TikTok's id and cover image via TikTok's public oEmbed.
    Without a cover the card is simply not shown."""
    if os.environ.get("SKIP_TIKTOK_LOOKUP"):
        return
    os.makedirs(os.path.join(DIST, "images", "tiktok"), exist_ok=True)
    for i, t in enumerate(TIKS):
        if t.get("video_id") and t.get("thumb"):
            continue
        try:
            src = t["url"] if not t.get("video_id") else f'https://www.tiktok.com/@{TT_HANDLE}/video/{t["video_id"]}'
            q = "https://www.tiktok.com/oembed?url=" + urllib.parse.quote(src, safe="")
            req = urllib.request.Request(q, headers={"User-Agent": "Mozilla/5.0 (site build)"})
            with urllib.request.urlopen(req, timeout=10) as res:
                d = json.loads(res.read().decode("utf-8"))
            m = re.search(r'data-video-id="(\d+)"', d.get("html", "")) or re.search(r"video/(\d+)", d.get("html", ""))
            vid = (m and m.group(1)) or str(d.get("embed_product_id") or "")
            if vid and not t.get("video_id"):
                t["video_id"] = vid
            thumb = d.get("thumbnail_url")
            if thumb and not t.get("thumb"):
                name = f"images/tiktok/tt-{i + 1}.jpg"
                req = urllib.request.Request(thumb, headers={"User-Agent": "Mozilla/5.0 (site build)"})
                with urllib.request.urlopen(req, timeout=10) as res, open(os.path.join(DIST, name), "wb") as f:
                    f.write(res.read())
                t["thumb"] = name
            print(f"TikTok {i + 1}: id={t.get('video_id') or '-'} thumb={'yes' if t.get('thumb') else 'no'}")
        except Exception as err:
            print(f"TikTok {i + 1}: lookup failed ({err.__class__.__name__}); card hidden")


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    shutil.copytree(os.path.join(ROOT, "src"), DIST, ignore=shutil.ignore_patterns("originals"))
    resolve_tiktoks()
    pages = {"index.html": page_home, "services.html": page_services, "gallery.html": page_gallery,
             "about.html": page_about, "contact.html": page_contact, "booking-received.html": page_received,
             "privacy.html": page_privacy, "404.html": page_404}
    if REVIEWS:
        pages["reviews.html"] = page_reviews
    for name, fn in pages.items():
        with open(os.path.join(DIST, name), "w", encoding="utf-8") as f:
            f.write(fn())
    listed = [p for p in pages if p not in ("booking-received.html", "404.html")]
    if NOINDEX:
        robots = "User-agent: *\nDisallow: /\n"
    else:
        robots = "User-agent: *\nAllow: /\n"
        if SITE_URL:
            urls = "".join(f"<url><loc>{e(SITE_URL)}/{'' if p == 'index.html' else p}</loc></url>" for p in listed)
            with open(os.path.join(DIST, "sitemap.xml"), "w") as f:
                f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
            robots += f"Sitemap: {SITE_URL}/sitemap.xml\n"
    with open(os.path.join(DIST, "robots.txt"), "w") as f:
        f.write(robots)
    print(f"Built {len(pages)} pages → dist/ (services: {len(OFFERED)}, photos: {len(PHOTOS)}, noindex: {NOINDEX}, site url: {SITE_URL or 'not set'})")


if __name__ == "__main__":
    main()
