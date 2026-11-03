#!/usr/bin/env python3
"""Static site generator for Amy African Hair Braiding And Boutique.

No dependencies: `python3 build.py` reads data/*.json and src/, writes dist/.
Set SITE_URL (env var or data/site.json "site_url") to add canonical URLs and the sitemap.
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
REVIEWS = [r for r in load("reviews.json")["reviews"] if r.get("text") and r.get("author")]
SITE_URL = (os.environ.get("SITE_URL") or S.get("site_url") or "").rstrip("/")
DRAFT = bool(S.get("draft_placeholders"))
OFFERED = [s for s in SERVICES["services"] if s.get("confirmed")]
e = lambda s: html.escape(str(s or ""), quote=True)
A = S["address"]
ADDR_LINE = f'{A["street"]}, {A["city"]}, {A["region"]} {A["postal"]}'
TEL = "tel:" + S["phone_e164"]
IG = S["instagram_url"]
TT = S.get("tiktok_url") or ""
TT_HANDLE = S.get("tiktok_handle") or ""
MAPS = S["google_maps_url"]

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
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "star": '<path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z" fill="currentColor" stroke="none"/>',
    "sparkle": '<path d="M12 3c.6 4.2 2.1 6.4 6 7-3.9.6-5.4 2.8-6 7-.6-4.2-2.1-6.4-6-7 3.9-.6 5.4-2.8 6-7z"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "heart": '<path d="M12 20s-7-4.4-9-8.6C1.5 8.2 3.4 5 6.6 5c2 0 3.4 1.1 4.4 2.6C12 6.1 13.4 5 15.4 5c3.2 0 5.1 3.2 3.6 6.4C19 15.6 12 20 12 20z"/>',
    "bag": '<path d="M5 8h14l-1 12H6z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "chat": '<path d="M21 12a8.5 8.5 0 0 1-12.6 7.4L3 21l1.6-5.2A8.5 8.5 0 1 1 21 12z"/>',
}


def ic(name, cls=""):
    return (f'<svg class="ic {cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{ICONS[name]}</svg>')


# ---------------------------------------------------------------- layout
NAV = [("index.html", "Home"), ("services.html", "Styles & Services"), ("gallery.html", "Gallery & Videos"),
       ("about.html", "About Amy"), ("reviews.html", "Reviews"), ("contact.html", "Contact")]


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
    if S.get("established"):
        ld["foundingDate"] = S["established"]
    if SITE_URL:
        ld["url"] = SITE_URL + "/"
        ld["image"] = SITE_URL + "/images/logo/og-image.jpg"
    if OFFERED:
        ld["makesOffer"] = [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": s["name"]}} for s in OFFERED]
    return json.dumps(ld, ensure_ascii=False)


def head(page, title, desc):
    canon = ""
    og_url = ""
    if SITE_URL:
        path = "" if page == "index.html" else page
        canon = f'<link rel="canonical" href="{e(SITE_URL + "/" + path)}">'
        og_url = f'<meta property="og:url" content="{e(SITE_URL + "/" + path)}"><meta property="og:image" content="{e(SITE_URL)}/images/logo/og-image.jpg">'
    full = f"{title} | {S['short_name']}" if page != "index.html" else title
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full)}</title>
<meta name="description" content="{e(desc)}">
{canon}
<meta property="og:type" content="website"><meta property="og:site_name" content="{e(S["name"])}">
<meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(desc)}">{og_url}
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#100810">
<link rel="icon" href="images/logo/favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="images/logo/favicon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500;1,600&family=Jost:wght@400;500;600&display=swap">
<link rel="stylesheet" href="assets/css/style.css">
<script type="application/ld+json">{json_ld()}</script>
</head>
<body data-page="{e(page)}">
<a class="skip" href="#main">Skip to content</a>
{header(page)}
<main id="main">
'''


def header(page):
    links = "".join(
        f'<li><a href="{h}"{" aria-current=\"page\"" if h == page else ""}>{e(t)}</a></li>' for h, t in NAV)
    return f'''<div class="topbar">
  <div class="wrap topbar-row">
    <a class="topbar-call" href="{TEL}">{ic("phone")}<span>Call us: <strong>{e(S["phone"])}</strong></span></a>
    <a class="topbar-addr hide-sm" href="{e(MAPS)}" target="_blank" rel="noopener">{ic("map")}<span>{e(ADDR_LINE)}</span></a>
  </div>
</div>
<header class="site-head" data-head>
  <div class="wrap head-row">
    <a class="brand" href="index.html" aria-label="{e(S["name"])}, home">
      <img src="images/logo/amy-logo-dark-480.webp" width="480" height="320" alt="{e(S["name"])} logo">
    </a>
    <nav class="nav" aria-label="Main">
      <ul id="nav-list" class="nav-list" data-nav>{links}</ul>
    </nav>
    <div class="head-cta">
      <a class="btn btn-ghost btn-sm hide-sm" href="{TEL}">{ic("phone")}<span>{e(S["phone"])}</span></a>
      <a class="btn btn-pink btn-sm" href="contact.html#book">Book</a>
      <button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav-list" data-menu>
        {ic("menu", "i-open")}{ic("close", "i-close")}<span class="sr">Menu</span>
      </button>
    </div>
  </div>
</header>'''


def foot():
    hours = hours_html()
    year = date.today().year
    return f'''</main>
<footer class="site-foot">
  <div class="wrap foot-grid">
    <div class="foot-brand">
      <img src="images/logo/amy-logo-dark-480.webp" width="480" height="320" alt="{e(S["name"])} logo" loading="lazy">
      <p class="foot-tag">Beautiful Hair. Beautiful Confidence. Beautiful Experience.</p>{f'<p class="foot-est">Est. {e(S["established"])}</p>' if S.get("established") else ""}
    </div>
    <div>
      <h2 class="foot-h">Visit</h2>
      <address><a href="{e(MAPS)}" target="_blank" rel="noopener">{e(A["street"])}<br>{e(A["city"])}, {e(A["region"])} {e(A["postal"])}</a></address>
      <p><a href="{TEL}">{e(S["phone"])}</a></p>
    </div>
    <div>
      <h2 class="foot-h">Hours</h2>
      {hours}
    </div>
    <div>
      <h2 class="foot-h">Explore</h2>
      <ul class="foot-links">{"".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in NAV)}
      <li><a href="{e(IG)}" target="_blank" rel="noopener">Instagram</a></li>{f'<li><a href="{e(TT)}" target="_blank" rel="noopener">TikTok</a></li>' if TT else ""}</ul>
    </div>
  </div>
  <div class="wrap foot-base">
    <p>© {year} {e(S["name"])} · {e(ADDR_LINE)}</p>
  </div>
</footer>
<nav class="mobile-bar{" has-tt" if TT else ""}" aria-label="Quick actions">
  <a href="{TEL}">{ic("phone")}<span>Call</span></a>
  <a href="contact.html#book" class="mb-book">{ic("calendar")}<span>Book</span></a>
  <a href="{e(IG)}" target="_blank" rel="noopener">{ic("instagram")}<span>Instagram</span></a>
  {f'<a href="{e(TT)}" target="_blank" rel="noopener">{ic("tiktok")}<span>TikTok</span></a>' if TT else ""}
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


def placeholder(label, note=""):
    if not DRAFT:
        return ""
    return f'<div class="ph" role="note"><strong>{e(label)}</strong>{f"<span>{e(note)}</span>" if note else ""}</div>'


def sec_head(eyebrow, title, lede="", center=False, h="h2"):
    c = " center" if center else ""
    return (f'<div class="sec-head{c} reveal"><p class="eyebrow">{ic("sparkle")}<span>{e(eyebrow)}</span></p>'
            f'<{h}>{title}</{h}>{f"<p class=lede>{lede}</p>" if lede else ""}</div>')


# ---------------------------------------------------------------- components
BRAID_ART = '''<svg class="braid-art" viewBox="0 0 120 200" aria-hidden="true" focusable="false"><defs><linearGradient id="g{n}" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#f3d77a"/><stop offset=".5" stop-color="#d4af37"/><stop offset="1" stop-color="#8a6a17"/></linearGradient></defs>
<g fill="none" stroke="url(#g{n})" stroke-width="5" stroke-linecap="round">
<path d="M40 10c30 15 30 25 0 40s-30 25 0 40 30 25 0 40-30 25 0 40"/><path d="M80 10c-30 15-30 25 0 40s30 25 0 40-30 25 0 40 30 25 0 40"/></g>
<rect x="49" y="96" width="22" height="14" rx="3" fill="url(#g{n})"/></svg>'''


def is_ill(src):
    return str(src or "").lower().endswith(".svg")


def service_img(s):
    src = s.get("image")
    if is_ill(src):
        return (f'<img src="{e(src)}" alt="Illustration of {e(s["name"].lower())}" width="400" height="300" loading="lazy" decoding="async">'
                '<span class="ill-tag">Illustration</span>')
    style = f' style="object-position:{e(s["image_position"])}"' if s.get("image_position") else ""
    if s.get("image_label"):
        return (f'<img src="{e(src)}" alt="Example of {e(s["name"].lower())}"{style} loading="lazy" decoding="async">'
                f'<span class="ill-tag">{e(s["image_label"])}</span>')
    return f'<img src="{e(src)}" alt="{e(s["name"])} by Amy African Hair Braiding"{style} loading="lazy" decoding="async">'


def style_previews(items):
    tiles = "".join(f'<figure class="style-tile reveal">{service_img(s)}<figcaption>{e(s["name"])}</figcaption></figure>'
                    for s in items if s.get("image"))
    return f'<div class="style-tiles">{tiles}</div>' if tiles else ""


def service_card(s, n, book=True, detail=False):
    img = (service_img(s)
           if s.get("image") else f'<div class="svc-art">{BRAID_ART.format(n=n)}<span class="svc-mono">{e(s["name"][0])}</span></div>')
    meta = []
    if s.get("duration"):
        meta.append(f'<li>{ic("clock")}<span>{e(s["duration"])}</span></li>')
    if s.get("price_from"):
        meta.append(f'<li><span>From {e(s["price_from"])}</span></li>')
    extra = ""
    if detail:
        rows = [(k, s.get(f)) for k, f in (("Lengths", "lengths"), ("Braid sizes", "sizes"))]
        dl = "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in rows if v)
        if dl:
            extra = f'<dl class="svc-dl">{dl}</dl>'
    q = urllib.parse.quote(s["name"])
    return f'''<article class="svc reveal" data-cat="{e(s["category"])}">
  <div class="svc-media">{img}</div>
  <div class="svc-body">
    <p class="svc-cat">{e(s["category"])}</p>
    <h3>{e(s["name"])}</h3>
    <p>{e(s["description"])}</p>
    {extra}
    {f'<ul class="svc-meta">{"".join(meta)}</ul>' if meta else '<p class="svc-note">Price and timing on request</p>'}
    {f'<a class="btn btn-line btn-sm" href="contact.html?style={q}#book">Book this style {ic("arrow")}</a>' if book else ""}
  </div>
</article>'''


def reel_card(r, i):
    title = r.get("title") or "Braiding by Amy"
    url = r.get("instagram_url", "")
    poster = r.get("poster", "")
    if r.get("mp4"):
        media = (f'<video class="reel-video" src="{e(r["mp4"])}" preload="none" controls muted playsinline '
                 f'{f"poster={chr(34)}{e(poster)}{chr(34)}" if poster else ""} aria-label="{e(title)}"></video>')
        return f'''<article class="reel reveal" data-kind="video">
  <div class="reel-frame">{media}</div>
  <div class="reel-cap"><h3>{e(title)}</h3>{f'<a href="{e(url)}" target="_blank" rel="noopener">View on Instagram {ic("external")}</a>' if url else ""}</div>
</article>'''
    bg = f'<img src="{e(poster)}" alt="" loading="lazy" decoding="async">' if poster else '<span class="reel-glow"></span>'
    return f'''<article class="reel reveal" data-kind="instagram" data-permalink="{e(url)}">
  <div class="reel-frame">
    <a class="reel-facade" href="{e(url)}" target="_blank" rel="noopener" aria-label="Watch “{e(title)}” on Instagram">
      {bg}
      <span class="reel-play">{ic("play")}</span>
      <span class="reel-status" data-status>Watch on Instagram</span>
    </a>
    <div class="reel-embed" data-embed></div>
  </div>
  <div class="reel-cap"><h3>{e(title)}</h3><a href="{e(url)}" target="_blank" rel="noopener">Open on Instagram {ic("external")}</a></div>
</article>'''


def resolve_tiktoks():
    """At build time (on Netlify, which can reach TikTok), look up each video's id and cover image
    through TikTok's public oEmbed endpoint, so every card gets a thumbnail and the player loads
    without relying on the visitor's browser. Any failure leaves that card as before."""
    if os.environ.get("SKIP_TIKTOK_LOOKUP"):
        return
    os.makedirs(os.path.join(DIST, "images", "tiktok"), exist_ok=True)
    for i, t in enumerate(TIKS):
        try:
            if not t.get("video_id") or not t.get("thumb"):
                q = "https://www.tiktok.com/oembed?url=" + urllib.parse.quote(t["url"], safe="")
                req = urllib.request.Request(q, headers={"User-Agent": "Mozilla/5.0 (site build)"})
                with urllib.request.urlopen(req, timeout=12) as res:
                    d = json.loads(res.read().decode("utf-8"))
                m = re.search(r'data-video-id="(\d+)"', d.get("html", "")) or re.search(r"video/(\d+)", d.get("html", ""))
                vid = (m and m.group(1)) or str(d.get("embed_product_id") or "")
                if vid and not t.get("video_id"):
                    t["video_id"] = vid
                thumb = d.get("thumbnail_url")
                if thumb and not t.get("thumb"):
                    name = f"images/tiktok/tt-{i + 1}.jpg"
                    req = urllib.request.Request(thumb, headers={"User-Agent": "Mozilla/5.0 (site build)"})
                    with urllib.request.urlopen(req, timeout=12) as res, open(os.path.join(DIST, name), "wb") as f:
                        f.write(res.read())
                    t["thumb"] = name
            print(f"TikTok {i + 1}: id={t.get('video_id') or '-'} thumb={'yes' if t.get('thumb') else 'no'}")
        except Exception as err:  # network or format problem: keep the link fallback
            print(f"TikTok {i + 1}: lookup failed ({err.__class__.__name__}); link fallback kept")


def tiktok_card(t):
    title = t.get("title") or "Amy on TikTok"
    url = t["url"]
    thumb = t.get("thumb") or ""
    poster = f'<img src="{e(thumb)}" alt="" loading="lazy" decoding="async">' if thumb else ""
    return f'''<article class="reel reveal" data-kind="tiktok" data-url="{e(url)}" data-vid="{e(t.get("video_id", ""))}" data-handle="{e(TT_HANDLE)}">
  <div class="reel-frame">
    <a class="reel-facade reel-facade-tt" href="{e(url)}" target="_blank" rel="noopener" aria-label="Watch “{e(title)}” on TikTok">
      <span class="reel-glow"></span>{poster}
      <span class="reel-play">{ic("play")}</span>
      <span class="reel-status" data-status>Watch on TikTok</span>
    </a>
    <div class="reel-embed reel-embed-tt" data-embed></div>
  </div>
  <div class="reel-cap"><h3>{e(title)}</h3><a href="{e(url)}" target="_blank" rel="noopener">Open on TikTok {ic("external")}</a></div>
</article>'''


def tiktok_block(home):
    if not TIKS:
        return ""
    items = [t for t in TIKS if t.get("home")][:3] if home else TIKS
    items = items or TIKS[:3]
    cls = "reels reels-home" if home else "reels reels-page"
    return (f'<div class="tt-head reveal"><p class="eyebrow">{ic("tiktok")}<span>On TikTok</span></p></div>'
            f'<div class="{cls}">{"".join(tiktok_card(t) for t in items)}</div>')


def reel_slots(n):
    if not DRAFT:
        return ""
    slot = ('<div class="reel reel-slot"><div class="reel-frame"><div class="reel-slot-in">{ic}<strong>Reel {i}</strong>'
            '<span>Paste a real Reel link in data/reels.json</span></div></div></div>')
    return "".join(slot.format(ic=ic("instagram"), i=i + 1) for i in range(n))


def follow_btn(label="Follow us on Instagram"):
    return f'<a class="btn btn-ig" href="{e(IG)}" target="_blank" rel="noopener">{ic("instagram")}<span>{e(label)}</span></a>'


def reels_section(home):
    items = [r for r in REELS if r.get("home")] if home else REELS
    if home and not items:
        items = REELS[:4]
    items = items[:4] if home else items[:9]
    if home:
        head_ = sec_head("On Instagram", "Watch Our <em>Braiding Magic</em>",
                         "Real work from the chair, straight from Amy’s Instagram.", center=True)
    else:
        head_ = sec_head("Videos", "Our Work <em>in Motion</em>",
                         "Short videos of finished styles and braiding in progress, from our Instagram.", center=True)
    if items:
        grid = "".join(reel_card(r, i) for i, r in enumerate(items))
    else:
        grid = reel_slots(3 if home else 6)
    cls = "reels reels-home" if home else "reels reels-page"
    empty = "" if items else (
        f'<p class="reels-empty reveal">Our newest braiding videos are on Instagram, <a href="{e(IG)}" target="_blank" rel="noopener">@{e(S["instagram_handle"])}</a>.</p>')
    more = f'<a class="btn btn-gold" href="{e(IG)}" target="_blank" rel="noopener">See more on Instagram {ic("arrow")}</a>' if home else follow_btn()
    if TT:
        more += f'<a class="btn btn-tt" href="{e(TT)}" target="_blank" rel="noopener">{ic("tiktok")}<span>Follow us on TikTok</span></a>'
    return f'''<section class="band band-dark reels-band" id="videos">
  <div class="wrap">
    {head_}
    {f'<div class="{cls}">{grid}</div>' if grid else ""}
    {empty}
    {tiktok_block(home)}
    <div class="center-row reveal">{more}</div>
  </div>
</section>'''


def review_card(r):
    stars = "".join(ic("star") for _ in range(int(r.get("rating") or 0)))
    return f'''<figure class="review reveal">
  {f'<div class="stars" aria-label="{e(r["rating"])} out of 5 stars">{stars}</div>' if stars else ""}
  <blockquote><p>{e(r["text"])}</p></blockquote>
  <figcaption><strong>{e(r["author"])}</strong><span>{e(r.get("source", "Google"))}{f" · {e(r['date'])}" if r.get("date") else ""}</span></figcaption>
</figure>'''


def booking_cta():
    return f'''<section class="band band-burgundy cta-band">
  <div class="wrap cta-in reveal">
    <h2>Your Next Beautiful Look <em>Starts Here.</em></h2>
    <p>Ready for a fresh style? Contact Amy African Hair Braiding And Boutique and let us help you find your next look.</p>
    <div class="btn-row center-row">
      <a class="btn btn-pink" href="contact.html#book">{ic("calendar")}<span>Book an Appointment</span></a>
      <a class="btn btn-ghost" href="{TEL}">{ic("phone")}<span>Call {e(S["phone"])}</span></a>
    </div>
  </div>
</section>'''


# ---------------------------------------------------------------- pages
def page_home():
    sig = [s for s in OFFERED if s.get("signature")][:6]
    why = [("Beautiful Results", "Careful braiding, attractive styles and attention to detail in every part."),
           ("Experienced Braiding", (f"Braiding since {S['established']}, with clients who describe coming back for years." if S.get("established") else "Clients describe coming back to Amy for years of satisfying service.")),
           ("Flexible Appointments", "Some clients have praised the salon for fitting in last-minute appointments."),
           ("Friendly Service", "Reviews describe a welcoming, professional experience from start to finish.")]
    home_reviews = [r for r in REVIEWS if r.get("home")][:3] or REVIEWS[:3]
    photos = GALLERY.get("photos", [])[:6]
    if photos:
        gal = '<div class="masonry">' + "".join(photo_item(p, i) for i, p in enumerate(photos)) + "</div>"
    else:
        gal = (style_previews(OFFERED[:4])
               + '<p class="ill-note reveal">Example photos of the styles we offer. Photos of Amy’s own work are coming soon.</p>'
               + f'<p class="center-row reveal">{follow_btn("See our latest styles on Instagram")}</p>')
    reviews_block = ("".join(review_card(r) for r in home_reviews)) if home_reviews else ""
    return head("index.html", "Amy African Hair Braiding And Boutique | Braids in St. Ann & St. Louis, MO",
                "African hair braiding in St. Ann, MO: braids, box braids, hair extensions and hairstyling near St. Louis. Call (314) 249-1615 or request an appointment online.") + f'''
<section class="hero">
  <div class="hero-bg" aria-hidden="true"></div>
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="eyebrow hero-eyebrow">{ic("map")}<span>{f"Est. {e(S['established'])} · " if S.get("established") else ""}St. Ann · St. Louis, Missouri</span></p>
      <h1>Beautiful Braids. <em>Bold Confidence.</em></h1>
      <p class="hero-lede">Discover stunning African braiding styles, beautiful transformations, and personalized hair care at Amy African Hair Braiding And Boutique in St. Ann, Missouri.</p>
      <div class="btn-row">
        <a class="btn btn-pink" href="contact.html#book">{ic("calendar")}<span>Book Your Appointment</span></a>
        <a class="btn btn-ghost" href="services.html">Explore Our Styles {ic("arrow")}</a>
      </div>
      <a class="hero-call" href="{TEL}">{ic("phone")}<span>Call now <strong>{e(S["phone"])}</strong></span></a>
    </div>
    <div class="hero-art">
      <div class="hero-logo">
        <picture>
          <source media="(max-width: 700px)" srcset="images/logo/amy-logo-dark-900.webp">
          <img src="images/logo/amy-logo-dark-1536.webp" width="1536" height="1024" alt="Amy African Hair Braiding And Boutique: braids, box braids, hair extensions, hairstyling" fetchpriority="high">
        </picture>
      </div>
    </div>
  </div>
  <ul class="hero-strip wrap" aria-label="Specialties">
    <li>Braids</li><li>Box Braids</li><li>Hair Extensions</li><li>Hairstyling</li>
  </ul>
</section>

<section class="band band-blush" id="styles">
  <div class="wrap">
    {sec_head("Signature styles", "Styles Made <em>for You</em>", "From classic braids to added length with extensions, each style is braided with care and finished to last.")}
    <div class="svc-grid">{"".join(service_card(s, i) for i, s in enumerate(sig))}</div>
    <div class="center-row reveal"><a class="btn btn-dark" href="services.html">See all styles & services {ic("arrow")}</a></div>
  </div>
</section>

<section class="band band-dark why-band">
  <div class="wrap">
    {sec_head("Why choose Amy", "Braiding with Heart <em>and Skill</em>", center=True)}
    <ul class="why">{"".join(f'<li class="reveal"><span class="why-n">0{i + 1}</span><h3>{e(t)}</h3><p>{e(d)}</p></li>' for i, (t, d) in enumerate(why))}</ul>
  </div>
</section>

<section class="band band-light" id="transformations">
  <div class="wrap">
    {sec_head("Featured work", "Every Braid Tells <em>a Beautiful Story.</em>", "Real styles from Amy’s chair." if photos else "A look at the styles we braid.", center=True)}
    {gal}
    {'<div class="center-row reveal"><a class="btn btn-dark" href="gallery.html">View all hairstyles ' + ic("arrow") + '</a></div>' if photos else ""}
  </div>
</section>

{reels_section(home=True)}

{f"""<section class="band band-blush"><div class="wrap">{sec_head("Kind words", "What Our <em>Clients Say</em>", center=True)}<div class="reviews">{reviews_block}</div>
<div class="center-row reveal"><a class="btn btn-dark" href="reviews.html">Read more reviews {ic("arrow")}</a></div></div></section>""" if reviews_block else ""}

{boutique_section()}

{booking_cta()}
''' + foot()


def boutique_section():
    b = S.get("boutique", {})
    if not b.get("show"):
        return ""
    cats = b.get("categories", [])
    note = "" if b.get("confirmed") else '<p class="muted small reveal">Ask in the salon about what is available today.</p>'
    q = urllib.parse.quote("Boutique inquiry")
    return f'''<section class="band band-dark boutique">
  <div class="wrap boutique-grid">
    <div class="reveal">
      <p class="eyebrow">{ic("bag")}<span>And Boutique</span></p>
      <h2>The <em>Boutique</em></h2>
      <p class="lede">Finishing touches to complete your look, available at the salon.</p>
      {note}
      <a class="btn btn-gold" href="contact.html?style={q}#book">Ask about the boutique {ic("arrow")}</a>
    </div>
    <ul class="boutique-cats">{"".join(f'<li class="reveal"><span>{ic("sparkle")}</span>{e(c)}</li>' for c in cats)}</ul>
  </div>
</section>'''


def page_services():
    cats = [c for c in SERVICES["filters"] if any(s["category"] == c for s in OFFERED)]
    filt = ('<div class="filters reveal" role="group" aria-label="Filter styles" data-filter-group="svc">'
            '<button type="button" class="chip" aria-pressed="true" data-filter="all">All</button>'
            + "".join(f'<button type="button" class="chip" aria-pressed="false" data-filter="{e(c)}">{e(c)}</button>' for c in cats)
            + "</div>") if len(cats) > 1 else ""
    faq = [f for f in S.get("faq", []) if f.get("a")]
    if faq:
        faq_html = '<div class="faq">' + "".join(
            f'<details class="reveal"><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in faq) + "</div>"
    else:
        faq_html = (placeholder("FAQ answers", "Answers appear once Amy confirms them in data/site.json → faq")
                    + f'<p class="lede reveal">Questions about hair preparation, timing, deposits or walk-ins? <a href="{TEL}">Call {e(S["phone"])}</a> and we’ll be happy to help.</p>')
    pending = [s for s in SERVICES["services"] if not s.get("confirmed")]
    pend = placeholder("Styles waiting for confirmation",
                       ", ".join(s["name"] for s in pending) + " — set confirmed: true in data/services.json to show them.") if pending else ""
    return head("services.html", "Hairstyles & Services",
                "Braids, box braids, hair extensions and hairstyling at Amy African Hair Braiding And Boutique in St. Ann, MO, near St. Louis.") + f'''
<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow">{ic("sparkle")}<span>Hairstyles & services</span></p>
    <h1>Find Your <em>Next Style</em></h1>
    <p class="lede">Browse the styles we offer, then request an appointment for the one you love.</p>
  </div>
</section>
<section class="band band-blush">
  <div class="wrap">
    {filt}
    <div class="svc-grid svc-grid-page" data-filter-target="svc">{"".join(service_card(s, i, detail=True) for i, s in enumerate(OFFERED))}</div>
    {pend}
  </div>
</section>
<section class="band band-light">
  <div class="wrap narrow">
    {sec_head("Good to know", "Frequently Asked <em>Questions</em>")}
    {faq_html}
  </div>
</section>
{boutique_section()}
{booking_cta()}
''' + foot()


def photo_item(p, i):
    w, h = p.get("width") or 900, p.get("height") or 1200
    return (f'<figure class="m-item reveal" data-cat="{e(p.get("style", ""))}"><button type="button" class="m-btn" data-lightbox="{e(p["src"])}" '
            f'data-alt="{e(p.get("alt", ""))}" aria-label="Enlarge: {e(p.get("alt", ""))}"><img src="{e(p["src"])}" width="{w}" height="{h}" alt="{e(p.get("alt", ""))}" loading="lazy" decoding="async"></button>'
            + (f"<figcaption>{e(p['style'])}</figcaption>" if p.get("style") else "") + "</figure>")


def page_gallery():
    photos = GALLERY.get("photos", [])
    styles = sorted({p.get("style") for p in photos if p.get("style")})
    filt = ('<div class="filters reveal" role="group" aria-label="Filter photos by style" data-filter-group="gal">'
            '<button type="button" class="chip" aria-pressed="true" data-filter="all">All</button>'
            + "".join(f'<button type="button" class="chip" aria-pressed="false" data-filter="{e(s)}">{e(s)}</button>' for s in styles)
            + "</div>") if len(styles) > 1 else ""
    if photos:
        grid = f'{filt}<div class="masonry" data-filter-target="gal">' + "".join(photo_item(p, i) for i, p in enumerate(photos)) + "</div>"
    else:
        grid = (style_previews(OFFERED)
                + '<p class="ill-note reveal">Example photos of the styles we offer. Our photo gallery of Amy’s own work is being prepared; see her latest styles on Instagram and TikTok.</p>'
                + f'<div class="center-row reveal">{follow_btn()}</div>')
    ba = GALLERY.get("before_after", [])
    ba_html = ""
    if ba:
        items = "".join(f'''<figure class="ba reveal"><div class="ba-frame" data-ba style="--pos:50%">
<img src="{e(x["after"])}" alt="After: {e(x.get("alt", ""))}" loading="lazy"><div class="ba-before"><img src="{e(x["before"])}" alt="Before: {e(x.get("alt", ""))}" loading="lazy"></div>
<input class="ba-range" type="range" min="0" max="100" value="50" aria-label="Compare before and after"><span class="ba-handle" aria-hidden="true"></span>
<span class="ba-tag ba-tag-b">Before</span><span class="ba-tag ba-tag-a">After</span></div>{f"<figcaption>{e(x.get('style'))}</figcaption>" if x.get("style") else ""}</figure>''' for x in ba)
        ba_html = f'<section class="band band-blush"><div class="wrap">{sec_head("Transformations", "Before <em>& After</em>", center=True)}<div class="ba-grid">{items}</div></div></section>'
    return head("gallery.html", "Gallery & Videos",
                "See real African braiding work by Amy African Hair Braiding And Boutique in St. Ann, MO: photos and videos of braids, box braids and more.") + f'''
<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow">{ic("sparkle")}<span>Gallery & videos</span></p>
    <h1>Real Braids, <em>Real Beauty</em></h1>
    <p class="lede">A look at the styles that leave our chair.</p>
    <div class="btn-row">{follow_btn()}</div>
  </div>
</section>
{reels_section(home=False)}
<section class="band band-light">
  <div class="wrap">
    {sec_head("Photos", "Every Braid Tells <em>a Beautiful Story.</em>", center=True)}
    {grid}
  </div>
</section>
{ba_html}
<div class="lightbox" data-lb hidden role="dialog" aria-modal="true" aria-label="Photo viewer">
  <button type="button" class="lb-close" data-lb-close aria-label="Close">{ic("close")}</button>
  <img alt="" data-lb-img>
</div>
{booking_cta()}
''' + foot()


def page_about():
    ab = S.get("about", {})
    photo = (f'<img class="about-photo" src="{e(ab["photo"])}" alt="Amy, owner of {e(S["name"])}" loading="lazy">'
             if ab.get("photo") else placeholder("Amy’s portrait", "Add her photo to src/images/about/ and set about.photo"))
    blocks = [("Her story", "story"), ("Her experience", "experience"), ("Her approach to care", "approach"),
              ("The salon & team", "team"), ("Her vision for the boutique", "vision")]
    out = []
    for title, key in blocks:
        v = ab.get(key)
        if v:
            paras = v if isinstance(v, list) else [v]
            out.append(f'<div class="about-block reveal"><h2>{e(title)}</h2>{"".join(f"<p>{e(p)}</p>" for p in paras)}</div>')
        else:
            ph = placeholder(title, "To be written with Amy, in her own words")
            if ph:
                out.append(ph)
    body = "".join(out)
    since = f", established in {e(S['established'])}," if S.get("established") else ""
    intro = (f'<p class="lede">Amy is the braider behind Amy African Hair Braiding And Boutique{since} in St. Ann, '
             'welcoming clients from across the St. Louis area for braids, extensions and styling.</p>')
    return head("about.html", "About Amy",
                "Meet Amy, the braider behind Amy African Hair Braiding And Boutique in St. Ann, Missouri.") + f'''
<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow">{ic("heart")}<span>About Amy</span></p>
    <h1>Meet Amy — <em>The Passion Behind the Braids.</em></h1>
    {intro}
  </div>
</section>
<section class="band band-light">
  <div class="wrap about-grid">
    <div class="about-media reveal">{photo or '<img class="about-photo about-logo" src="images/logo/amy-logo-light-900.webp" alt="Amy African Hair Braiding And Boutique logo" loading="lazy">'}</div>
    <div class="about-copy">{body or f'<p class="lede reveal">Come and meet Amy at the salon, or follow her work on Instagram.</p><div class="btn-row">{follow_btn()}</div>'}</div>
  </div>
</section>
{booking_cta()}
''' + foot()


def page_reviews():
    rt = S.get("google_rating", {})
    rating = ""
    if rt.get("show"):
        rating = (f'<div class="rating reveal"><span class="rating-v">{e(rt["value"])}</span><div><div class="stars">{ic("star")}</div>'
                  f'<p>Google rating from {e(rt["count"])} reviews, as of {e(rt["as_of"])}</p></div></div>')
    cards = "".join(review_card(r) for r in REVIEWS)
    body = (f'<div class="reviews">{cards}</div>' if cards
            else placeholder("Client testimonials", "Add real Google reviews word for word in data/reviews.json"))
    return head("reviews.html", "Reviews",
                "Read client reviews of Amy African Hair Braiding And Boutique in St. Ann, MO, and share your own experience on Google.") + f'''
<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow">{ic("star")}<span>Reviews</span></p>
    <h1>Kind Words <em>from Our Clients</em></h1>
    <p class="lede">See what clients say about their braids, and read every review on Google.</p>
    <div class="btn-row">
      <a class="btn btn-dark" href="{e(S["google_reviews_url"])}" target="_blank" rel="noopener">Read all reviews on Google {ic("external")}</a>
    </div>
  </div>
</section>
<section class="band band-blush">
  <div class="wrap">
    {rating}
    {body}
  </div>
</section>
<section class="band band-dark">
  <div class="wrap center reveal leave">
    <h2>Loved your braids?</h2>
    <p class="lede">Your review helps other clients find us. Thank you for sharing your honest experience.</p>
    <a class="btn btn-gold" href="{e(S["google_reviews_url"])}" target="_blank" rel="noopener">{ic("star")}<span>Leave a Google review</span></a>
  </div>
</section>
''' + foot()


def page_contact():
    opts = "".join(f'<option value="{e(s["name"])}">{e(s["name"])}</option>' for s in OFFERED)
    pol = S.get("policies", {})
    pol_items = [(t, pol.get(k)) for t, k in (("Deposits", "deposit"), ("Cancellations", "cancellation"),
                                              ("Late arrivals", "late_arrival"), ("Hair preparation", "hair_preparation"))]
    pol_html = "".join(f'<div><h3>{e(t)}</h3><p>{e(v)}</p></div>' for t, v in pol_items if v)
    if not pol_html:
        pol_html = placeholder("Booking policies", "Deposits, cancellations, late arrivals and hair preparation — add Amy’s policies in data/site.json")
    wa = (f'<li><a class="contact-tile" href="https://wa.me/{e(S["whatsapp_number"])}" target="_blank" rel="noopener">{ic("chat")}<span><strong>WhatsApp</strong>Message us</span></a></li>'
          if S.get("whatsapp_number") else "")
    sec_phone = f'<p>Also: <a href="tel:{e(S["phone_secondary"])}">{e(S["phone_secondary"])}</a></p>' if S.get("phone_secondary") else ""
    park = f'<p class="muted">{e(S["parking"])}</p>' if S.get("parking") else ""
    map_q = urllib.parse.quote(f'{S["name"]}, {ADDR_LINE}')
    return head("contact.html", "Contact & Book an Appointment",
                "Request a braiding appointment at Amy African Hair Braiding And Boutique, 10007 St Charles Rock Rd, St Ann, MO 63074. Call (314) 249-1615.") + f'''
<section class="page-hero">
  <div class="wrap">
    <p class="eyebrow">{ic("calendar")}<span>Contact & booking</span></p>
    <h1>Book Your <em>Appointment</em></h1>
    <p class="lede">Send a request below and we’ll contact you to confirm a time, or call us directly.</p>
    <ul class="contact-tiles">
      <li><a class="contact-tile" href="{TEL}">{ic("phone")}<span><strong>Call</strong>{e(S["phone"])}</span></a></li>
      <li><a class="contact-tile" href="#book">{ic("calendar")}<span><strong>Request</strong>Booking form</span></a></li>
      <li><a class="contact-tile" href="{e(IG)}" target="_blank" rel="noopener">{ic("instagram")}<span><strong>Instagram</strong>@{e(S["instagram_handle"])}</span></a></li>
      {f'<li><a class="contact-tile" href="{e(TT)}" target="_blank" rel="noopener">{ic("tiktok")}<span><strong>TikTok</strong>@{e(TT_HANDLE)}</span></a></li>' if TT else ""}
      {wa}
    </ul>
  </div>
</section>

<section class="band band-blush" id="book">
  <div class="wrap book-grid">
    <form class="book-form reveal" name="booking" method="POST" action="booking-received.html" enctype="multipart/form-data"
          data-netlify="true" netlify-honeypot="company" data-book data-phone="{e(S["phone"])}" novalidate>
      <input type="hidden" name="form-name" value="booking">
      <p class="hp"><label>Leave this empty <input name="company" tabindex="-1" autocomplete="off"></label></p>
      <h2>Appointment request</h2>
      <p class="muted small">This is a request, not a confirmed appointment. We’ll contact you to confirm availability.</p>
      <div class="f2">
        <div class="f"><label for="b-name">Your name *</label><input id="b-name" name="name" autocomplete="name" required></div>
        <div class="f"><label for="b-phone">Phone number *</label><input id="b-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" required pattern="[0-9+()\\-\\s.]{{7,}}"></div>
      </div>
      <div class="f"><label for="b-email">Email <span class="opt">(optional)</span></label><input id="b-email" name="email" type="email" autocomplete="email"></div>
      <div class="f"><label for="b-style">Hairstyle requested *</label>
        <select id="b-style" name="style" required><option value="">Choose a style…</option>{opts}<option value="Not sure yet">Not sure yet / something else</option><option value="Boutique inquiry">Boutique inquiry</option></select></div>
      <div class="f2">
        <div class="f"><label for="b-date">Preferred date *</label><input id="b-date" name="date" type="date" required></div>
        <div class="f"><label for="b-time">Preferred time *</label>
          <select id="b-time" name="time" required><option value="">Choose…</option><option>Morning</option><option>Midday</option><option>Afternoon</option><option>Evening</option><option>I’m flexible</option></select></div>
      </div>
      <div class="f"><label for="b-size">Hair length or braid size</label><input id="b-size" name="length_size" placeholder="e.g. medium, waist length"></div>
      <div class="f"><label for="b-details">Additional details</label><textarea id="b-details" name="details" rows="4" placeholder="Colors, hair you’re bringing, anything we should know"></textarea></div>
      <div class="f"><label for="b-photo">Inspiration photo <span class="opt">(optional, JPG or PNG, max 8 MB)</span></label>
        <input id="b-photo" name="inspiration_photo" type="file" accept="image/jpeg,image/png,image/webp,image/heic"></div>
      <p class="form-msg" data-msg role="status" aria-live="polite"></p>
      <button class="btn btn-pink btn-block" type="submit" data-submit>{ic("calendar")}<span>Send my request</span></button>
      <p class="muted small">Your details are used only to arrange your appointment.</p>
    </form>
    <aside class="visit reveal">
      <h2>Visit the salon</h2>
      <address><a href="{e(MAPS)}" target="_blank" rel="noopener">{ic("map")}<span>{e(S["name"])}<br>{e(A["street"])}<br>{e(A["city"])}, {e(A["region"])} {e(A["postal"])}</span></a></address>
      <p><a class="big-tel" href="{TEL}">{ic("phone")}{e(S["phone"])}</a></p>
      {sec_phone}
      <h3>Hours</h3>
      {hours_html()}
      {park}
      <a class="btn btn-dark btn-block" href="{e(MAPS)}" target="_blank" rel="noopener">{ic("map")}<span>Get directions</span></a>
      <div class="map"><iframe title="Map to {e(S["name"])}" src="https://www.google.com/maps?q={map_q}&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>
    </aside>
  </div>
</section>
<section class="band band-light">
  <div class="wrap narrow">
    {sec_head("Before you book", "Booking <em>Policies</em>")}
    <div class="policies">{pol_html}</div>
  </div>
</section>
''' + foot()


def page_received():
    return head("booking-received.html", "Request received", "Your appointment request was received.").replace(
        '<meta name="description"', '<meta name="robots" content="noindex"><meta name="description"', 1) + f'''
<section class="page-hero page-hero-tall">
  <div class="wrap center">
    <p class="eyebrow">{ic("check")}<span>Request received</span></p>
    <h1>Thank you!</h1>
    <p class="lede">Your appointment request has been received. Our team will contact you to confirm availability.</p>
    <div class="btn-row center-row"><a class="btn btn-ghost" href="index.html">Back to home</a><a class="btn btn-pink" href="{TEL}">{ic("phone")}<span>Call {e(S["phone"])}</span></a></div>
  </div>
</section>
''' + foot()


def page_404():
    return head("404.html", "Page not found", "This page could not be found.").replace(
        '<meta name="description"', '<meta name="robots" content="noindex"><meta name="description"', 1) + f'''
<section class="page-hero page-hero-tall">
  <div class="wrap center">
    <h1>Page <em>not found</em></h1>
    <p class="lede">The page you’re looking for doesn’t exist. Let’s get you back to beautiful braids.</p>
    <div class="btn-row center-row"><a class="btn btn-pink" href="index.html">Go to home</a></div>
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
    if SITE_URL:
        urls = "".join(f"<url><loc>{e(SITE_URL)}/{'' if p == 'index.html' else p}</loc></url>"
                       for p in pages if p not in ("booking-received.html", "404.html"))
        with open(os.path.join(DIST, "sitemap.xml"), "w") as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
        robots += f"Sitemap: {SITE_URL}/sitemap.xml\n"
    with open(os.path.join(DIST, "robots.txt"), "w") as f:
        f.write(robots)
    print(f"Built {len(pages)} pages → dist/ (reels: {len(REELS)}, services shown: {len(OFFERED)}, draft placeholders: {DRAFT}, site url: {SITE_URL or 'not set'})")


if __name__ == "__main__":
    main()
