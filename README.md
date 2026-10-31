# Amy African Hair Braiding And Boutique — website

Six pages (Home, Styles & Services, Gallery & Videos, About Amy, Reviews, Contact & Booking), plus a booking confirmation page and a 404 page.
Built as a fast static site with no dependencies: `python3 build.py` turns the files in `data/` and `src/` into `dist/`.

## Put it online (Netlify)
**Option A — GitHub (recommended):** push this folder to a GitHub repo, then in Netlify: Add new project → Import from GitHub. `netlify.toml` already sets the build (`python3 build.py`) and publish folder (`dist`).
**Option B — drag and drop:** run `python3 build.py`, then drag the `dist` folder onto app.netlify.com/drop.

After the first deploy:
1. **Forms → enable form detection**, then **Forms → booking → Notifications → Email** to Amy’s verified address. Requests (and inspiration photos) are stored privately in Netlify.
2. Send one real test request from a phone and check it arrives.
3. Connect the domain, then set `"site_url": "https://yourdomain.com"` in `data/site.json`. This adds canonical tags, Open Graph URLs and `sitemap.xml`.

## Edit content (no code)
| What | File |
|---|---|
| Instagram Reels (homepage + Gallery) | `data/reels.json` |
| Styles, prices, durations | `data/services.json` (`confirmed: true` to show a style) |
| Photos and before/after pairs | `data/gallery.json` + files in `src/images/gallery/` |
| Google reviews | `data/reviews.json` (exact words only) |
| Phone, hours, policies, FAQ, About text | `data/site.json` |

### Adding a Reel
In Instagram: open the Reel → ••• → Copy link. Add to `data/reels.json`:
```json
{"title": "Knotless braids, waist length", "instagram_url": "https://www.instagram.com/reel/ABC123xyz/", "style": "Knotless Braids", "home": true, "poster": "", "mp4": ""}
```
- `home: true` puts it in the homepage section (3–4 recommended). All Reels show on Gallery & Videos (6–9 recommended).
- Embeds load only when scrolled into view, using Instagram’s official embed. Instagram embeds never autoplay. If a post can’t be embedded (embedding turned off, post private or deleted), the card stays as a styled “Watch on Instagram” link.
- To check a Reel can be embedded: on instagram.com open the post → ••• → **Embed** should be available.
- **Switching to original video files later:** put `video.mp4` in `src/videos/` and a cover in `src/images/video-posters/`, then set `"mp4": "videos/video.mp4", "poster": "images/video-posters/video.jpg"`. Same layout; muted, inline, with controls, and only one plays at a time.

### Launch checklist
Set `"draft_placeholders": false` in `data/site.json` once content is in. This hides every dashed “To complete” box. Then confirm: hours (don’t use Google’s 24-hour listing), second phone number, which extra styles Amy offers, prices/durations, FAQ answers, policies, Amy’s photo and bio, review quotes and the exact Google review link, WhatsApp (only if used for business), boutique items.

Nothing on the site invents prices, durations, reviews, transformations or biography. Use only real photos and videos of Amy’s work, with client permission where faces are shown.
