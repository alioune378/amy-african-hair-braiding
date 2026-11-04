#!/usr/bin/env python3
"""Static site generator for Amy African Hair Braiding And Boutique.

No dependencies: `python3 build.py` reads data/*.json and src/, writes dist/.
Set SITE_URL (env var or data/site.json "site_url") to add canonical URLs and the sitemap.

Content rules built into the generator:
- Only styles marked confirmed: true in data/services.json are shown.
- Example photos are always labelled "Style example"; they are never presented as Amy's work.
- Empty fields (hours, policies, FAQ answers, About text, reviews, boutique items) are hidden, never
  replaced with placeholder or invented text.
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
BEFORE_AFTER = [x for x in GALLERY.get("before_after", []) if x.get("before") and x.get("after")]
REVIEWS = [r for r in load("reviews.json")["reviews"] if r.get("text") and r.get("author")]
SITE_URL = (os.environ.get("SITE_URL") or S.get("site_url") or "").rstrip("/")
OFFERED = [s for s in SERVICES["services"] if s.get("confirmed")]
e = lambda s: html.escape(str(s or ""), quote=True)
A = S["address"]
ADDR_LINE = f'{A["street"]}, {A["city"]}, {A["region"]} {A["postal"]}'
TEL = "tel:" + S["phone_e164"]
IG = S["instagram_url"]
IG_HANDLE = S.get("instagram_handle") or ""
TT = S.get("tiktok_url") or ""
TT_HANDLE = S.get("tiktok_handle") or ""
MAPS = S["google_maps_url"]
EST = S.get("established") or ""
OG_IMAGE = S.get("share_image") or "images/logo/og-image.jpg"
HERO = S.get("hero") or {}
ABOUT = S.get("about") or {}
BOUTIQUE = S.get("boutique") or {}

# ---------------------------------------------------------------- icons
ICONS = {
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "instagram": '<rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".6" fill="currentColor"/>',
    "tiktok": '<path d="M14 3v11.5a3.5 3.5 0 1 1-3.5-3.5"/><path d="M14 3c.4 2.6 2.2 4.4 5 4.6"/>',
    "map": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "play": '<path d="M7 4.5v15l13-7.5z" fill="currentColor" stroke="none"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "star": '<path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z" fill="currentColor" stroke="none"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "chat": '<path d="M21 12a8.5 8.5 0 0 1-12.6 7.4L3 21l1.6-5.2A8.5 8.5 0 1 1 21 12z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "left": '<path d="M15 5l-7 7 7 7"/>',
    "right": '<path d="M9 5l7 7-7 7"/>',
}


def ic(name, cls=""):
    return (f'<svg class="ic {cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[name]}</svg>')


# ---------------------------------------------------------------- layout
NAV = [("index.html", "Home"), ("services.html", "Services"), ("gallery.html", "Our Work"), ("about.html", "About Amy")]
if REVIEWS:
    NAV.append(("reviews.html", "Reviews"))
NAV.append(("contact.html", "Contact"))


def json_ld():
    ld = {
        "@context": "https://schema.org", "@type": "HairSalon", "name": S["name"],
        "telephone": S["phone_e164"],
        "address": {"@type": "PostalAddress", "streetAddress": A["street"], "addressLocality": A["city"],
                    "addressRegion": A["region"], "postalCode": A["postal"], "addressCountry": A["country"]},
        "areaServed": ["St. Ann, MO", "St. Louis, MO"],
        "sameAs": [u for u in (IG, TT) if u],
        "hasMap": MAPS,
    }
    if EST:
        ld["foundingDate"] = EST
    if SITE_URL:
        ld["url"] = SITE_URL + "/"
        ld["image"] = SITE_URL + "/" + OG_IMAGE
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
                  f'<meta property="og:image:height" content="630"><meta property="og:image:alt" content="Braids by Amy: long box braids, blonde boho braids and feed-in braids">'
                  f'<meta name="twitter:image" content="{e(SITE_URL)}/{OG_IMAGE}">')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{canon}
<meta property="og:type" content="website"><meta property="og:site_name" content="{e(S["name"])}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">{og_url}
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#120a10">
<link rel="icon" href="images/logo/favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="images/logo/favicon-192.png">
<link rel="preload" href="assets/fonts/cormorant.woff" as="font" type="font/woff" crossorigin>
<link rel="preload" href="assets/fonts/jost.woff" as="font" type="font/woff" crossorigin>{preload}
<link rel="stylesheet" href="assets/css/style.css">
<script type="application/ld+json">{json_ld()}</script>
</head>
<body data-page="{e(page)}">
<a class="skip" href="#main">Skip to content</a>
{header(page)}
<main id="main" tabindex="-1">
'''


def header(page):
    links = "".join(
        f'<li><a href="{h}"{" aria-current=\"page\"" if h == page else ""}>{e(t)}</a></li>' for h, t in NAV)
    social = (f'<a href="{e(IG)}" target="_blank" rel="noopener">{ic("instagram")}<span>Instagram</span></a>'
              + (f'<a href="{e(TT)}" target="_blank" rel="noopener">{ic("tiktok")}<span>TikTok</span></a>' if TT else ""))
    return f'''<header class="site-head" data-head>
  <div class="wrap head-row">
    <a class="brand" href="index.html" aria-label="{e(S["name"])}, home">
      <img src="images/logo/amy-logo-dark-240.webp" srcset="images/logo/amy-logo-dark-240.webp 240w, images/logo/amy-logo-dark-480.webp 480w" sizes="96px" width="240" height="160" alt="{e(S["name"])} logo">
    </a>
    <nav class="nav-desk" aria-label="Main">
      <ul>{links}</ul>
    </nav>
    <div class="head-cta">
      <a class="head-tel" href="{TEL}">{ic("phone")}<span>{e(S["phone"])}</span></a>
      <a class="btn btn-pink btn-sm head-book" href="contact.html#book">Book</a>
      <button class="menu-btn" type="button" aria-expanded="false" aria-controls="menu" data-menu-open>
        {ic("menu")}<span class="sr">Open menu</span>
      </button>
    </div>
  </div>
</header>
<div class="menu" id="menu" role="dialog" aria-modal="true" aria-label="Menu" hidden data-menu>
  <div class="menu-top">
    <img src="images/logo/amy-logo-dark-240.webp" width="240" height="160" alt="" class="menu-logo">
    <button class="menu-close" type="button" data-menu-close>{ic("close")}<span class="sr">Close menu</span></button>
  </div>
  <nav aria-label="Main"><ul class="menu-list">{links}</ul></nav>
  <div class="menu-actions">
    <a class="btn btn-pink btn-block" href="contact.html#book">{ic("calendar")}<span>Book an appointment</span></a>
    <a class="btn btn-ghost btn-block" href="{TEL}">{ic("phone")}<span>Call {e(S["phone"])}</span></a>
  </div>
  <div class="menu-social">{social}</div>
</div>'''


def foot():
    year = date.today().year
    social = (f'<li><a href="{e(IG)}" target="_blank" rel="noopener">Instagram</a></li>'
              + (f'<li><a href="{e(TT)}" target="_blank" rel="noopener">TikTok</a></li>' if TT else ""))
    return f'''</main>
<footer class="site-foot" data-foot>
  <div class="wrap foot-grid">
    <div class="foot-brand">
      <img src="images/logo/amy-logo-dark-480.webp" width="480" height="320" alt="{e(S["name"])} logo" loading="lazy">
      {f'<p class="foot-est">African hair braiding in St. Ann since {e(EST)}</p>' if EST else ""}
    </div>
    <div>
      <h2 class="foot-h">Visit</h2>
      <address><a href="{e(MAPS)}" target="_blank" rel="noopener">{e(A["street"])}<br>{e(A["city"])}, {e(A["region"])} {e(A["postal"])}</a></address>
      <p><a href="{TEL}">{e(S["phone"])}</a></p>
    </div>
    <div>
      <h2 class="foot-h">Hours</h2>
      {hours_html()}
    </div>
    <div>
      <h2 class="foot-h">Explore</h2>
      <ul class="foot-links">{"".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in NAV)}{social}</ul>
    </div>
  </div>
  <div class="wrap foot-base"><p>© {year} {e(S["name"])} · {e(ADDR_LINE)}</p></div>
</footer>
<nav class="mbar" aria-label="Quick actions" data-mbar>
  <a class="mbar-call" href="{TEL}">{ic("phone")}<span>Call</span></a>
  <a class="mbar-book" href="contact.html#book">{ic("calendar")}<span>Book appointment</span></a>
</nav>
<script src="assets/js/site.js" defer></script>
</body>
</html>
'''


def hours_html():
    if S.get("hours"):
        rows = "".join(f"<li><span>{e(d)}</span><span>{e(h)}</span></li>" for d, h in S["hours"])
        return f'<ul class="hours">{rows}</ul>'
    return f'<p class="muted">Please call to confirm today’s hours.<br><a href="{TEL}">{e(S["phone"])}</a></p>'


def sec_head(eyebrow, title, lede="", center=False):
    c = " center" if center else ""
    return (f'<div class="sec-head{c}"><p class="eyebrow">{e(eyebrow)}</p>'
            f'<h2>{title}</h2>{f"<p class=lede>{lede}</p>" if lede else ""}</div>')


def is_example(src, label):
    return bool(label) or str(src or "").lower().endswith(".svg")


def book_link(name, label="Book this style", cls="btn btn-line btn-sm"):
    return f'<a class="{cls}" href="contact.html?style={urllib.parse.quote(name)}#book">{e(label)} {ic("arrow")}</a>'


# ---------------------------------------------------------------- components
def service_card(s):
    src = s.get("image") or ""
    media = ""
    if src and not src.lower().endswith(".svg"):
        pos = f' style="object-position:{e(s["image_position"])}"' if s.get("image_position") else ""
        tag = f'<span class="tag-example">{e(s.get("image_label") or "Style example")}</span>' if s.get("image_label") else ""
        alt = f'Example of {s["name"].lower()}' if s.get("image_label") else f'{s["name"]} by Amy'
        media = f'<div class="svc-media"><img src="{e(src)}" alt="{e(alt)}"{pos} loading="lazy" decoding="async">{tag}</div>'
    meta = []
    if s.get("duration"):
        meta.append(f'{ic("clock")}<span>{e(s["duration"])}</span>')
    price = f'From {e(s["price_from"])}' if s.get("price_from") else "Price on request"
    return f'''<article class="svc" data-cat="{e(s["category"])}">
  {media}
  <div class="svc-body">
    <h3>{e(s["name"])}</h3>
    <p>{e(s["description"])}</p>
    <p class="svc-meta">{"".join(meta)}<span>{price}</span></p>
    {book_link(s["name"])}
  </div>
</article>'''


def service_row(s):
    """Compact home-page item: no image, so the hero photo is never repeated nearby."""
    return f'''<li class="svc-row">
  <a href="contact.html?style={urllib.parse.quote(s["name"])}#book">
    <span class="svc-row-t">{e(s["name"])}</span>
    <span class="svc-row-d">{e(s["description"])}</span>
    <span class="svc-row-a">Book {ic("arrow")}</span>
  </a>
</li>'''


def reel_card(r):
    title = r.get("title") or "Braiding by Amy"
    url = r.get("instagram_url", "")
    poster = r.get("poster", "")
    if r.get("mp4"):
        return f'''<li class="reel" data-kind="video">
  <div class="reel-frame"><video src="{e(r["mp4"])}" preload="none" controls muted playsinline{f' poster="{e(poster)}"' if poster else ""} aria-label="{e(title)}"></video></div>
  <div class="reel-cap"><h3>{e(title)}</h3>{f'<a href="{e(url)}" target="_blank" rel="noopener">Instagram {ic("external")}</a>' if url else ""}</div>
</li>'''
    bg = f'<img src="{e(poster)}" alt="" loading="lazy" decoding="async">' if poster else ""
    return f'''<li class="reel" data-kind="instagram" data-permalink="{e(url)}">
  <div class="reel-frame">
    <button class="reel-facade" type="button" data-load aria-label="Play “{e(title)}” (Instagram)">
      {bg}<span class="reel-play">{ic("play")}</span><span class="reel-src">{ic("instagram")}Instagram</span><span class="reel-status" data-status>Tap to play</span>
    </button>
    <div class="reel-embed" data-embed></div>
  </div>
  <div class="reel-cap"><h3>{e(title)}</h3><a href="{e(url)}" target="_blank" rel="noopener">Open post {ic("external")}</a></div>
</li>'''


def resolve_tiktoks():
    """At build time, try TikTok's public oEmbed endpoint for each video's id and cover image.
    Video ids written in data/tiktoks.json always take priority. Any failure keeps the link card."""
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
            print(f"TikTok {i + 1}: lookup failed ({err.__class__.__name__}); link card kept")


def tiktok_card(t):
    title = t.get("title") or "Amy on TikTok"
    url = t["url"]
    thumb = t.get("thumb") or ""
    bg = f'<img src="{e(thumb)}" alt="" loading="lazy" decoding="async">' if thumb else ""
    return f'''<li class="reel" data-kind="tiktok" data-url="{e(url)}" data-vid="{e(t.get("video_id", ""))}">
  <div class="reel-frame">
    <button class="reel-facade" type="button" data-load aria-label="Play “{e(title)}” (TikTok)">
      {bg}<span class="reel-play">{ic("play")}</span><span class="reel-src">{ic("tiktok")}TikTok</span><span class="reel-status" data-status>Tap to play</span>
    </button>
    <div class="reel-embed" data-embed></div>
  </div>
  <div class="reel-cap"><h3>{e(title)}</h3><a href="{e(url)}" target="_blank" rel="noopener">Open on TikTok {ic("external")}</a></div>
</li>'''


def video_showcase(home):
    """One carousel mixing Instagram and TikTok. Nothing third-party loads until a visitor taps play."""
    ig = [r for r in REELS if r.get("home")] if home else REELS
    tt = [t for t in TIKS if t.get("home")] if home else TIKS
    if home:
        ig, tt = (ig or REELS)[:3], (tt or TIKS)[:3]
    cards = []
    for i in range(max(len(ig), len(tt))):  # alternate the two platforms
        if i < len(ig):
            cards.append(reel_card(ig[i]))
        if i < len(tt):
            cards.append(tiktok_card(tt[i]))
    if not cards:
        return ""
    follow = (f'<a class="btn btn-ghost" href="{e(IG)}" target="_blank" rel="noopener">{ic("instagram")}<span>@{e(IG_HANDLE)}</span></a>'
              + (f'<a class="btn btn-ghost" href="{e(TT)}" target="_blank" rel="noopener">{ic("tiktok")}<span>@{e(TT_HANDLE)}</span></a>' if TT else ""))
    title = "Fresh from <em>the chair</em>" if home else "Our work <em>in motion</em>"
    lede = ("Real videos of Amy’s work, from her Instagram and TikTok."
            if home else "Every video here is Amy’s own work, posted on her Instagram and TikTok. Tap a video to play it.")
    more = f'<a class="btn btn-gold" href="gallery.html">See all videos {ic("arrow")}</a>' if home else ""
    return f'''<section class="band band-dark" id="videos" aria-labelledby="videos-h">
  <div class="wrap">
    <div class="sec-head sec-head-row">
      <div><p class="eyebrow">Our work</p><h2 id="videos-h">{title}</h2><p class="lede">{lede}</p></div>
      <div class="car-nav" aria-hidden="false">
        <button type="button" class="car-btn" data-car-prev aria-label="Previous videos">{ic("left")}</button>
        <button type="button" class="car-btn" data-car-next aria-label="Next videos">{ic("right")}</button>
      </div>
    </div>
  </div>
  <ul class="reels" data-carousel tabindex="0" aria-label="Videos">{"".join(cards)}</ul>
  <div class="wrap btn-row center-row">{more}{follow}</div>
</section>'''


def photo_srcset(p):
    if not p.get("base") or not p.get("widths"):
        return ""
    return ", ".join(f'{e(p["base"])}-{w}.webp {w}w' for w in p["widths"])


def look_link(p):
    q = urllib.parse.urlencode({"style": p.get("book_as") or "", "look": p.get("alt") or ""})
    return f"contact.html?{q}#book"


def photo_item(p, sizes="(max-width: 699px) 50vw, (max-width: 1099px) 33vw, 380px"):
    w, h = p.get("width") or 900, p.get("height") or 1200
    alt = p.get("alt", "")
    ss = photo_srcset(p)
    big = f'{p["base"]}-{p["widths"][-1]}.webp' if ss else p["src"]
    source = f'<source type="image/webp" srcset="{ss}" sizes="{sizes}">' if ss else ""
    img = f'<picture>{source}<img src="{e(p["src"])}" width="{w}" height="{h}" alt="{e(alt)}" loading="lazy" decoding="async"></picture>'
    link = look_link(p) if p.get("book_as") else ""
    book = f'<a class="m-book" href="{e(link)}">Book this look {ic("arrow")}</a>' if link else ""
    cap = f'<p class="m-cap">{e(p["style"])}</p>' if p.get("style") else ""
    return (f'<li class="m-item" data-cat="{e(p.get("style", ""))}"><button type="button" class="m-btn" data-lightbox="{e(big)}" '
            f'data-alt="{e(alt)}" data-cap="{e(p.get("style", ""))}" data-book="{e(link)}" aria-label="Enlarge photo: {e(alt)}">{img}</button>'
            f'<div class="m-meta">{cap}{book}</div></li>')


def review_card(r):
    stars = "".join(ic("star") for _ in range(int(r.get("rating") or 0)))
    return f'''<figure class="review">
  {f'<div class="stars" aria-label="{e(r["rating"])} out of 5 stars">{stars}</div>' if stars else ""}
  <blockquote><p>{e(r["text"])}</p></blockquote>
  <figcaption><strong>{e(r["author"])}</strong><span>{e(r.get("source", "Google"))}{f" · {e(r['date'])}" if r.get("date") else ""}</span></figcaption>
</figure>'''


def booking_cta():
    return f'''<section class="band band-burgundy cta-band">
  <div class="wrap cta-in">
    <h2>Ready for your <em>next look?</em></h2>
    <p>Send a request online or call the salon. We’ll get back to you to confirm a time.</p>
    <div class="btn-row center-row">
      <a class="btn btn-pink" href="contact.html#book">{ic("calendar")}<span>Book an appointment</span></a>
      <a class="btn btn-ghost" href="{TEL}">{ic("phone")}<span>Call {e(S["phone"])}</span></a>
    </div>
  </div>
</section>'''


def boutique_section():
    if not BOUTIQUE.get("show"):
        return ""
    items = [i for i in BOUTIQUE.get("items", []) if i.get("name") and i.get("image")]
    grid = ""
    if items:
        grid = '<ul class="bq-grid">' + "".join(
            f'<li class="bq-item"><img src="{e(i["image"])}" alt="{e(i["name"])}" loading="lazy" decoding="async"><h3>{e(i["name"])}</h3>'
            + (f"<p>{e(i['note'])}</p>" if i.get("note") else "") + "</li>" for i in items) + "</ul>"
    cats = BOUTIQUE.get("categories", []) if BOUTIQUE.get("confirmed") else []
    cat_line = f'<p class="bq-cats">{" · ".join(e(c) for c in cats)}</p>' if cats else ""
    return f'''<section class="band band-ink boutique" aria-labelledby="bq-h">
  <div class="wrap bq-in">
    <div>
      <p class="eyebrow">And boutique</p>
      <h2 id="bq-h">The <em>boutique</em></h2>
      <p class="lede">Finishing touches for your new style are available at the salon. Ask what’s in store today during your visit, or send us a question.</p>
      {cat_line}
      {book_link("Boutique inquiry", "Ask about the boutique", "btn btn-gold")}
    </div>
    {grid}
  </div>
</section>'''


def hero_media():
    src = HERO.get("image")
    if not src:
        return ""
    tag = '<span class="tag-example">Style example</span>' if HERO.get("image_is_example") else ""
    w, h = HERO.get("image_width") or 900, HERO.get("image_height") or 1125
    srcset = f' srcset="{e(HERO["srcset"])}" sizes="(max-width: 859px) 78vw, 400px"' if HERO.get("srcset") else ""
    pos = f' style="object-position:{e(HERO["position"])}"' if HERO.get("position") else ""
    cap = "" if HERO.get("image_is_example") else '<figcaption class="hero-cap">Box braids by Amy</figcaption>'
    return (f'<figure class="hero-media"><img src="{e(src)}"{srcset} width="{w}" height="{h}" alt="{e(HERO.get("alt") or "Braided hairstyle")}"{pos} '
            f'fetchpriority="high" decoding="async">{tag}{cap}</figure>')


# ---------------------------------------------------------------- pages
def page_home():
    why = [("Since " + EST if EST else "Experienced", "Braiding in St. Ann for over a decade." if EST else "Years of braiding experience."),
           ("Attention to detail", "Clean parts, even tension and a neat finish."),
           ("Made for you", "Size, length and style chosen with you."),
           ("Beautiful results", "Real styles by Amy, in photos and videos.")]
    home_reviews = ([r for r in REVIEWS if r.get("home")][:3] or REVIEWS[:3])
    reviews_block = ""
    if home_reviews:
        reviews_block = f'''<section class="band band-light"><div class="wrap">{sec_head("Kind words", "What our <em>clients say</em>", center=True)}
<div class="reviews">{"".join(review_card(r) for r in home_reviews)}</div>
<div class="center-row"><a class="btn btn-dark" href="reviews.html">Read more reviews {ic("arrow")}</a></div></div></section>'''
    photos = [p for p in PHOTOS if p.get("home")][:6] or PHOTOS[:6]
    photos_block = ""
    if photos:
        photos_block = f'''<section class="band band-light crafted" aria-labelledby="crafted-h"><div class="wrap">
<div class="sec-head center"><p class="eyebrow">Real work by Amy</p><h2 id="crafted-h">Crafted by Amy. <em>Worn with confidence.</em></h2>
<p class="lede">Discover the skill, precision and creativity behind every style. These are real hairstyles created by Amy for her clients.</p></div>
<ul class="masonry masonry-home">{"".join(photo_item(p, "(max-width: 699px) 50vw, 380px") for p in photos)}</ul>
<div class="center-row"><a class="btn btn-dark" href="gallery.html">Explore Amy’s work {ic("arrow")}</a></div></div></section>'''
    preload = f'<link rel="preload" as="image" href="{e(HERO["image"])}">' if HERO.get("image") else ""
    return head("index.html", "Amy African Hair Braiding | Braids in St. Ann & St. Louis, MO",
                f"African hair braiding in St. Ann, MO, near St. Louis: braids, box braids, hair extensions and styling. Call {S['phone']} or request an appointment online.",
                preload) + f'''
<section class="hero" aria-labelledby="hero-h">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="eyebrow">{ic("map")}<span>St. Ann · St. Louis, MO{f" · Since {e(EST)}" if EST else ""}</span></p>
      <h1 id="hero-h">Braids, done <em>beautifully.</em></h1>
      <p class="hero-lede">African hair braiding, extensions and styling on St. Charles Rock Road in St. Ann, just outside St. Louis.</p>
      <div class="btn-row">
        <a class="btn btn-pink" href="contact.html#book">{ic("calendar")}<span>Book appointment</span></a>
        <a class="btn btn-ghost" href="{TEL}">{ic("phone")}<span>Call the salon</span></a>
      </div>
      <a class="hero-link" href="services.html">Explore styles {ic("arrow")}</a>
    </div>
    {hero_media()}
  </div>
</section>

<section class="band band-light" aria-labelledby="svc-h">
  <div class="wrap svc-home">
    <div class="sec-head">
      <p class="eyebrow">Services</p>
      <h2 id="svc-h">What we <em>braid</em></h2>
      <p class="lede">Every style is quoted for you, based on size, length and the hair used.</p>
    </div>
    <ul class="svc-rows">{"".join(service_row(s) for s in OFFERED)}</ul>
  </div>
</section>

{photos_block}

<section class="why" aria-label="Why choose Amy">
  <ul class="wrap why-list">{"".join(f'<li><strong>{e(t)}</strong><span>{e(d)}</span></li>' for t, d in why)}</ul>
</section>

{video_showcase(home=True)}
{reviews_block}
{boutique_section()}
{booking_cta()}
''' + foot()


def page_hero(eyebrow, title, lede, extra=""):
    return f'''<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow">{e(eyebrow)}</p>
    <h1>{title}</h1>
    <p class="lede">{lede}</p>{extra}
  </div>
</section>'''


def page_services():
    faq = [f for f in S.get("faq", []) if f.get("a")]
    faq_html = ""
    if faq:
        faq_html = f'''<section class="band band-light"><div class="wrap narrow">{sec_head("Good to know", "Questions & <em>answers</em>")}
<div class="faq">{"".join(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in faq)}</div></div></section>'''
    any_example = any(s.get("image_label") for s in OFFERED)
    note = ('<p class="note">Photos marked “Style example” show the style, not Amy’s own work. '
            'See her real work on the <a href="gallery.html">Our Work</a> page.</p>') if any_example else ""
    return head("services.html", "Braiding Services in St. Ann, MO | Amy African Hair Braiding",
                "Braids, box braids, hair extensions and hairstyling at Amy African Hair Braiding And Boutique in St. Ann, MO, near St. Louis. Price on request.") + page_hero(
        "Services", "Find your <em>next style</em>",
        "Choose a style and request an appointment. Prices depend on size, length and hair, so every quote is personal.") + f'''
<section class="band band-light">
  <div class="wrap">
    <div class="svc-grid">{"".join(service_card(s) for s in OFFERED)}</div>
    {note}
    <p class="center-row"><a class="btn btn-dark" href="contact.html?style={urllib.parse.quote("Not sure yet")}#book">Not sure which style? Ask us {ic("arrow")}</a></p>
  </div>
</section>
{faq_html}
{boutique_section()}
{booking_cta()}
''' + foot()


CAT_ORDER = ["Box Braids", "Feed-In Braids / Cornrows", "Boho & Goddess-Inspired Braids", "Twists & Curly Styles", "Other Braiding Styles"]


def page_gallery():
    photos_html = ""
    if PHOTOS:
        styles = sorted({p.get("style") for p in PHOTOS if p.get("style")}, key=lambda c: CAT_ORDER.index(c) if c in CAT_ORDER else 99)
        filt = ('<div class="filters" role="group" aria-label="Filter photos by style" data-filter-group="gal">'
                '<button type="button" class="chip" aria-pressed="true" data-filter="all">All</button>'
                + "".join(f'<button type="button" class="chip" aria-pressed="false" data-filter="{e(c)}">{e(c)}</button>' for c in styles)
                + "</div>") if len(styles) > 1 else ""
        photos_html = f'''<section class="band band-light" id="portfolio" aria-label="Portfolio"><div class="wrap">
<p class="real-badge">{ic("check")}<span>Real clients. Real styles. Real work by Amy.</span></p>
{filt}<ul class="masonry" data-filter-target="gal">{"".join(photo_item(p) for p in PHOTOS)}</ul>
<div class="love">
  <h2>Love this look? <em>Let’s create yours.</em></h2>
  <p>Tap “Book this look” under any photo and Amy will know which style inspired you.</p>
  <a class="btn btn-pink" href="contact.html#book">{ic("calendar")}<span>Book your appointment</span></a>
</div></div></section>'''
    ba_html = ""
    if BEFORE_AFTER:
        items = "".join(f'''<figure class="ba"><div class="ba-frame" data-ba style="--pos:50%">
<img src="{e(x["after"])}" alt="After: {e(x.get("alt", ""))}" loading="lazy"><div class="ba-before"><img src="{e(x["before"])}" alt="Before: {e(x.get("alt", ""))}" loading="lazy"></div>
<input class="ba-range" type="range" min="0" max="100" value="50" aria-label="Compare before and after"><span class="ba-handle" aria-hidden="true"></span>
<span class="ba-tag ba-tag-b">Before</span><span class="ba-tag ba-tag-a">After</span></div>{f"<figcaption>{e(x.get('style'))}</figcaption>" if x.get("style") else ""}</figure>''' for x in BEFORE_AFTER)
        ba_html = f'<section class="band band-light"><div class="wrap">{sec_head("Transformations", "Before <em>& after</em>", center=True)}<div class="ba-grid">{items}</div></div></section>'
    lb = ('<div class="lightbox" data-lb hidden role="dialog" aria-modal="true" aria-label="Photo viewer">'
          f'<div class="lb-top"><span class="lb-count" data-lb-count></span><button type="button" class="lb-close" data-lb-close aria-label="Close">{ic("close")}</button></div>'
          '<figure class="lb-fig"><img alt="" data-lb-img><figcaption><span class="lb-cap" data-lb-cap></span>'
          f'<a class="btn btn-pink btn-sm" data-lb-book href="contact.html#book">Book this look</a></figcaption></figure>'
          f'<button type="button" class="lb-nav lb-prev" data-lb-prev aria-label="Previous photo">{ic("left")}</button>'
          f'<button type="button" class="lb-nav lb-next" data-lb-next aria-label="Next photo">{ic("right")}</button></div>') if PHOTOS else ""
    return head("gallery.html", "Amy’s Work: Box Braids, Feed-Ins, Boho Braids & Twists | St. Ann, MO",
                "Real hairstyles by Amy African Hair Braiding in St. Ann, MO: box braids, feed-in braids, boho braids and curly twists. Photos and videos of her work.") + page_hero(
        "Portfolio", "The art of braiding. <em>The beauty of you.</em>",
        "Every braid tells a story. Explore real hairstyles beautifully crafted by Amy, from intricate feed-in braids to flowing box braids and elegant twists.") + f'''
{photos_html}
{video_showcase(home=False)}
{ba_html}
{lb}
{booking_cta()}
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
    since = f" since {e(EST)}" if EST else ""
    photo = (f'<img class="about-photo" src="{e(ABOUT["photo"])}" alt="Amy, owner of {e(S["name"])}" loading="lazy">'
             if ABOUT.get("photo") else "")
    facts = f'''<dl class="facts">
  {f"<div><dt>Established</dt><dd>{e(EST)}</dd></div>" if EST else ""}
  <div><dt>Salon</dt><dd>{e(A["street"])}, {e(A["city"])}, {e(A["region"])}</dd></div>
  <div><dt>Specialties</dt><dd>{", ".join(e(s["name"]) for s in OFFERED)}</dd></div>
  <div><dt>Follow</dt><dd><a href="{e(IG)}" target="_blank" rel="noopener">Instagram</a>{f' · <a href="{e(TT)}" target="_blank" rel="noopener">TikTok</a>' if TT else ""}</dd></div>
</dl>'''
    intro = (f'<p class="about-lede">Amy African Hair Braiding And Boutique has welcomed clients on St. Charles Rock Road in St. Ann{since}, '
             f'braiding for women and girls from across the St. Louis area. The salon offers {", ".join(s["name"].lower() for s in OFFERED[:-1])} '
             f'and {OFFERED[-1]["name"].lower()}, with a small boutique for finishing touches.</p>'
             '<p>The best way to know Amy’s work is to see it: her newest styles are posted on Instagram and TikTok, '
             'and gathered on our <a href="gallery.html">Our Work</a> page.</p>') if OFFERED else ""
    return head("about.html", "About Amy | African Hair Braiding in St. Ann, MO",
                f"Meet Amy African Hair Braiding And Boutique, braiding in St. Ann, MO{since}, for clients across the St. Louis area.") + page_hero(
        "About", "The salon behind <em>the braids</em>",
        f"A braiding salon in St. Ann, Missouri{since}.") + f'''
<section class="band band-light">
  <div class="wrap about-grid">
    <div class="about-copy">
      {intro}
      {"".join(out)}
      <div class="btn-row"><a class="btn btn-dark" href="gallery.html">See Amy’s work {ic("arrow")}</a></div>
    </div>
    <aside class="about-side">{photo}{facts}</aside>
  </div>
</section>
{booking_cta()}
''' + foot()


def page_reviews():
    rt = S.get("google_rating", {})
    rating = ""
    if rt.get("show"):
        rating = (f'<div class="rating"><span class="rating-v">{e(rt["value"])}</span><div><div class="stars">{ic("star")}</div>'
                  f'<p>Google rating from {e(rt["count"])} reviews, as of {e(rt["as_of"])}</p></div></div>')
    cards = "".join(review_card(r) for r in REVIEWS)
    body = f'<div class="reviews">{cards}</div>' if cards else ""
    return head("reviews.html", "Reviews | Amy African Hair Braiding, St. Ann, MO",
                "Client reviews of Amy African Hair Braiding And Boutique in St. Ann, MO. Read and leave reviews on Google.") + page_hero(
        "Reviews", "Kind words <em>from our clients</em>",
        "Read what clients say on Google, and share your own experience.",
        f'<div class="btn-row"><a class="btn btn-dark" href="{e(S["google_reviews_url"])}" target="_blank" rel="noopener">Reviews on Google {ic("external")}</a></div>') + f'''
<section class="band band-light"><div class="wrap">{rating}{body}</div></section>
''' + foot()


def page_contact():
    opts = "".join(f'<option value="{e(s["name"])}">{e(s["name"])}</option>' for s in OFFERED)
    pol = S.get("policies", {})
    pol_items = [(t, pol.get(k)) for t, k in (("Deposits", "deposit"), ("Cancellations", "cancellation"),
                                              ("Late arrivals", "late_arrival"), ("Hair preparation", "hair_preparation"))]
    pol_html = "".join(f'<div><h3>{e(t)}</h3><p>{e(v)}</p></div>' for t, v in pol_items if v)
    pol_section = (f'<section class="band band-light"><div class="wrap narrow">{sec_head("Before you book", "Booking <em>policies</em>")}'
                   f'<div class="policies">{pol_html}</div></div></section>') if pol_html else ""
    wa = (f'<a class="contact-line" href="https://wa.me/{e(S["whatsapp_number"])}" target="_blank" rel="noopener">{ic("chat")}<span>WhatsApp</span></a>'
          if S.get("whatsapp_number") else "")
    sec_phone = f'<p>Also: <a href="tel:{e(S["phone_secondary"])}">{e(S["phone_secondary"])}</a></p>' if S.get("phone_secondary") else ""
    park = f'<p class="muted">{e(S["parking"])}</p>' if S.get("parking") else ""
    return head("contact.html", "Book an Appointment | Amy African Hair Braiding, St. Ann, MO",
                f"Request a braiding appointment at Amy African Hair Braiding And Boutique, {ADDR_LINE}. Call {S['phone']}.") + page_hero(
        "Book", "Request an <em>appointment</em>",
        "Tell us the style and the day you’d like. We’ll contact you to confirm a time. Prefer to talk? Call the salon.",
        f'<div class="btn-row"><a class="btn btn-ghost-dark" href="{TEL}">{ic("phone")}<span>Call {e(S["phone"])}</span></a></div>') + f'''
<section class="band band-light" id="book">
  <div class="wrap book-grid">
    <form class="book-form" name="booking" method="POST" action="booking-received.html" enctype="multipart/form-data"
          data-netlify="true" netlify-honeypot="company" data-book data-phone="{e(S["phone"])}" novalidate>
      <input type="hidden" name="form-name" value="booking">
      <p class="hp" aria-hidden="true"><label>Leave this empty <input name="company" tabindex="-1" autocomplete="off"></label></p>
      <h2>Appointment request</h2>
      <p class="form-intro">{ic("clock")}<span>This is a request, not a confirmed booking. We’ll call or text you to confirm.</span></p>
      <div class="f2">
        <div class="f"><label for="b-name">Your name</label><input id="b-name" name="name" autocomplete="name" required aria-describedby="b-name-err"><p class="f-err" id="b-name-err"></p></div>
        <div class="f"><label for="b-phone">Phone number</label><input id="b-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" required pattern="[0-9+()\\-\\s.]{{7,}}" aria-describedby="b-phone-err"><p class="f-err" id="b-phone-err"></p></div>
      </div>
      <div class="f"><label for="b-style">Hairstyle</label>
        <select id="b-style" name="style" required aria-describedby="b-style-err"><option value="">Choose a style…</option>{opts}<option value="Not sure yet">Not sure yet</option><option value="Boutique inquiry">Boutique question</option></select><p class="f-err" id="b-style-err"></p></div>
      <div class="f2">
        <div class="f"><label for="b-date">Preferred date</label><input id="b-date" name="date" type="date" required aria-describedby="b-date-err"><p class="f-err" id="b-date-err"></p></div>
        <div class="f"><label for="b-time">Preferred time</label>
          <select id="b-time" name="time" required aria-describedby="b-time-err"><option value="">Choose…</option><option>Morning</option><option>Midday</option><option>Afternoon</option><option>Evening</option><option>I’m flexible</option></select><p class="f-err" id="b-time-err"></p></div>
      </div>
      <div class="f"><label for="b-photo">Inspiration photo <span class="opt">optional · up to 8 MB</span></label>
        <input id="b-photo" name="inspiration_photo" type="file" accept="image/jpeg,image/png,image/webp,image/heic,image/heif"><p class="f-err" id="b-photo-err"></p></div>
      <div class="f"><label for="b-details">Additional details <span class="opt">optional</span></label><textarea id="b-details" name="details" rows="3" placeholder="Length, size, color, hair you’re bringing…"></textarea></div>
      <p class="form-msg" data-msg role="status" aria-live="polite"></p>
      <button class="btn btn-pink btn-block" type="submit" data-submit>{ic("calendar")}<span>Send my request</span></button>
      <p class="privacy">Your details are used only to arrange your appointment. They are never shared or used for marketing.</p>
    </form>
    <aside class="visit">
      <h2>Visit the salon</h2>
      <address><a href="{e(MAPS)}" target="_blank" rel="noopener">{ic("map")}<span>{e(S["name"])}<br>{e(A["street"])}<br>{e(A["city"])}, {e(A["region"])} {e(A["postal"])}</span></a></address>
      <a class="contact-line" href="{TEL}">{ic("phone")}<span>{e(S["phone"])}</span></a>
      {sec_phone}
      <a class="contact-line" href="{e(IG)}" target="_blank" rel="noopener">{ic("instagram")}<span>@{e(IG_HANDLE)}</span></a>
      {f'<a class="contact-line" href="{e(TT)}" target="_blank" rel="noopener">{ic("tiktok")}<span>@{e(TT_HANDLE)}</span></a>' if TT else ""}
      {wa}
      <h3>Hours</h3>
      {hours_html()}
      {park}
      <a class="btn btn-gold btn-block" href="{e(MAPS)}" target="_blank" rel="noopener">{ic("map")}<span>Get directions</span></a>
    </aside>
  </div>
</section>
{pol_section}
''' + foot()


def page_received():
    return head("booking-received.html", "Request received | Amy African Hair Braiding",
                "Your appointment request has been received.") + f'''
<section class="page-hero page-hero-tall">
  <div class="wrap narrow center">
    <p class="eyebrow">{ic("check")}<span>Request received</span></p>
    <h1>Thank you, <em>we’ve got it.</em></h1>
    <p class="lede">Your appointment request has been sent to the salon. It isn’t a confirmed booking yet: we’ll call or text you to confirm a time.</p>
    <div class="btn-row center-row">
      <a class="btn btn-pink" href="{TEL}">{ic("phone")}<span>Call {e(S["phone"])}</span></a>
      <a class="btn btn-ghost-dark" href="index.html">Back to home</a>
    </div>
  </div>
</section>
''' + foot()


def page_404():
    return head("404.html", "Page not found | Amy African Hair Braiding", "This page could not be found.") + f'''
<section class="page-hero page-hero-tall">
  <div class="wrap narrow center">
    <h1>Page <em>not found</em></h1>
    <p class="lede">The page you’re looking for has moved. Try the home page, or book an appointment.</p>
    <div class="btn-row center-row"><a class="btn btn-pink" href="contact.html#book">Book appointment</a><a class="btn btn-ghost-dark" href="index.html">Home</a></div>
  </div>
</section>
''' + foot()


# ---------------------------------------------------------------- build
def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    shutil.copytree(os.path.join(ROOT, "src"), DIST)
    resolve_tiktoks()
    pages = {"index.html": page_home, "services.html": page_services, "gallery.html": page_gallery,
             "about.html": page_about, "reviews.html": page_reviews, "contact.html": page_contact,
             "booking-received.html": page_received, "404.html": page_404}
    for name, fn in pages.items():
        with open(os.path.join(DIST, name), "w", encoding="utf-8") as f:
            f.write(fn())
    robots = "User-agent: *\nAllow: /\n"
    listed = [p for p in pages if p not in ("booking-received.html", "404.html") and (p != "reviews.html" or REVIEWS)]
    if SITE_URL:
        urls = "".join(f"<url><loc>{e(SITE_URL)}/{'' if p == 'index.html' else p}</loc></url>" for p in listed)
        with open(os.path.join(DIST, "sitemap.xml"), "w") as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
        robots += f"Sitemap: {SITE_URL}/sitemap.xml\n"
    with open(os.path.join(DIST, "robots.txt"), "w") as f:
        f.write(robots)
    print(f"Built {len(pages)} pages → dist/ (instagram: {len(REELS)}, tiktok: {len(TIKS)}, services: {len(OFFERED)}, photos: {len(PHOTOS)}, site url: {SITE_URL or 'not set'})")


if __name__ == "__main__":
    main()
