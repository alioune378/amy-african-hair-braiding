# Before production launch (Nov 2026 redesign)

**Launch blockers**
1. **Booking delivery not yet proven.** The site posts requests to Netlify Forms (form "booking"). Netlify showed 0 submissions. In Netlify → Forms → booking → Notifications, add Amy's email. Then send one real request from a phone and confirm it arrives. The new fields (`braid_size`, `length`, `selected_look`) register on the next deploy. No SMS or customer email confirmation is configured; customers see the on-screen confirmation page only.
2. **Phone numbers.** The site shows (314) 249-1615 everywhere. (314) 429-2823 appears only as a small "Also" line on the home Visit section and the Contact page. The storefront sign shows (314) 395-7624. Confirm with Amy which secondary number is current.
3. **Domain.** After amyafricanbraids.com is purchased and connected, set `"site_url": "https://amyafricanbraids.com"` and `"noindex": false` in `data/site.json`. The preview is currently kept out of search engines.

**Content to confirm**
- Opening hours (the site says "Please call to confirm today's hours")
- Year established (the wall sign shows EST 2019 in some photos and 2010 in others; hidden until confirmed)
- A proper portrait of Amy (Meet Amy currently uses a still from her salon video)
- Genuine Google reviews to quote (the section stays hidden until added)
- Boutique items and photos (the section stays compact until added)
- Instagram Reel cover images (`poster` in `data/reels.json`). Reels appear in the video gallery only once they have a real cover. TikTok covers are fetched automatically when Netlify builds.
- Prices and durations, if Amy wants them shown

---

# Content still needed from Amy

The site shows only confirmed information. Anything missing is hidden, never filled with placeholder text.

0. **Confirm the year the salon opened.** The wall sign reads **"EST 2019"** in the earlier photos (green light) but appears to read **"EST 2010"** in the Nov 2026 photos (red light). Until confirmed, no year is shown anywhere ("Since …" is hidden in the hero, footer, About page and Google data). Put the correct year in `established` in `data/site.json`.
0b. **Confirm the storefront photo.** "Visit Amy's Salon" uses the retouched storefront version with the OPEN sign (`src/images/salon/`). Its sign shows (314) 249-1615 and **(314) 395-7624**. Confirm the photo is accurate, and whether 395-7624 is still active (it is not used as a contact number on the site). The version with "314-429-2823" printed twice in the window was not used: it looks like an editing artifact.
0c. **Dalal Technologies link.** The footer credit is unlinked. Add the verified web address in `data/site.json` → `developer_credit.url`.
0d. **Booking emails (launch blocker).** Netlify shows the "booking" form with 0 submissions ever. Set the email notification (below), then send one real request from a phone and confirm it arrives. The new optional **Email** field registers on the next deploy.

1. **Real photos:** 16 of Amy's photos are now live. Still needed, with client permission where faces show:
   - A photo for **Hairstyling** (updos and buns). The card currently has no picture rather than an unrelated one.
   - Cleaner replacements for two photos held back: `11_Feeding_Braids_Alternate_Closeup` (it has app icons and a pixelated band across the face) and `17_Curly_Twist_Braids_Portrait` (motion blur).
   - Optional: higher-quality versions of photos 12–18. They are video stills and slightly soft.
   - Confirm the name she uses for the curly twist style (passion twists, spring twists, …). It's shown as "Curly Twists".
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
