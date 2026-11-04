# Content still needed from Amy

The site shows only confirmed information. Anything missing is hidden, never filled with placeholder text.

1. **Real photos of her work**, with client permission where faces show:
   - A hero photo (portrait, about 900×1125 px). Set it in `data/site.json` → `hero.image`, with `image_is_example: false`.
   - One photo per service (`data/services.json` → `image`, and empty `image_label`).
   - 6–12 portfolio photos (`data/gallery.json`). Real before/after pairs are optional.
2. **TikTok full links.** Open each video, then Share → Copy link, and paste it in a browser so the address shows `/video/<number>`. Put the number in `data/tiktoks.json` → `video_id`. With it, the player loads reliably and the build can fetch the cover image.
3. **Instagram cover images (optional):** a screenshot of each Reel's first frame, set as `poster` in `data/reels.json`. Without one, the card shows the branded play cover.
4. **Hours** (`data/site.json` → `hours`). Until then the site says "Please call to confirm today's hours".
5. **Other styles she offers:** knotless braids, cornrows, twists and so on. Set `confirmed: true` in `data/services.json`.
6. **Prices or starting prices and durations**, if she wants them shown. Otherwise "Price on request" stays.
7. **Booking policies:** deposit, cancellation, late arrival and hair preparation (`data/site.json` → `policies`). The section appears only when filled.
8. **FAQ answers** (`data/site.json` → `faq`).
9. **Her story, in her own words**, and a portrait if she wants one (`data/site.json` → `about`).
10. **Google reviews** to quote word for word (`data/reviews.json`). The Reviews page and nav link appear only when there's at least one.
11. **Boutique:** real items with photos (`data/site.json` → `boutique.items`), and confirmation of the categories.
12. **Second phone number** shown on Instagram, (314) 429-2823, if it should appear.
13. **Domain:** set `site_url` in `data/site.json` to enable canonical tags and the sitemap.

## Booking form delivery (Netlify)
The form "booking" is registered on the site. To receive requests by email:
1. In Netlify, go to **Forms → booking → Form notifications → Add notification → Email notification**.
2. Enter Amy's email.
3. Send one test request from a phone and confirm it arrives.

Requests and inspiration photos are also stored privately in Netlify → Forms.
