# MOB-C01 — Progressive Web App (PWA) manifest + installability

## Context

Abu Oracle runs on `app.abu-oracle.com` — a Next.js app. Users primarily access it on desktop,
but mobile usage is growing. Converting to an installable PWA gives:

- "Add to Home Screen" on iOS Safari and Android Chrome
- Splash screen + standalone window (no browser chrome)
- Offline-friendly (chart data already persists in Zustand/localStorage)
- Push notification readiness (future — for daily mundana content)

This is a **pure frontend task** — no backend changes required.

## Files to create / modify

```
next_app/public/manifest.json          NEW
next_app/public/icons/                 NEW — icon set (see sizes below)
next_app/app/layout.tsx                MODIFY — add PWA meta tags
next_app/next.config.js (or .ts)       MODIFY — add headers for manifest MIME type
```

## Spec

### 1. `public/manifest.json`

```json
{
  "name": "Abu Oracle",
  "short_name": "Abu Oracle",
  "description": "Computational astrology — natal chart, HF relocation map, and Lilly interpretation.",
  "start_url": "/chart",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#f59e0b",
  "orientation": "portrait-primary",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "screenshots": [],
  "categories": ["productivity", "lifestyle"],
  "lang": "es"
}
```

Colors match the existing design system:
- `background_color`: `slate-900` (#0f172a)
- `theme_color`: `amber-400` (#f59e0b)

### 2. Icon files

Place in `next_app/public/icons/`:
- `icon-192.png` — 192×192 px — the Abu Oracle logo (existing `assets/social/logos/abu_oracle_logo_v1.png`, resized)
- `icon-512.png` — 512×512 px — same, higher resolution
- `icon-512-maskable.png` — 512×512 px — padded 10% safe area on all sides (for Android adaptive icons)

**How to generate** (add to a `scripts/generate_icons.py` helper):
```python
from PIL import Image
import os

src = "assets/social/logos/abu_oracle_logo_v1.png"
out_dir = "next_app/public/icons"
os.makedirs(out_dir, exist_ok=True)

img = Image.open(src).convert("RGBA")
for size in [192, 512]:
    img.resize((size, size), Image.LANCZOS).save(f"{out_dir}/icon-{size}.png")

# Maskable: 10% padding on all sides
padded_size = 512
pad = int(padded_size * 0.1)
inner = padded_size - 2 * pad
bg = Image.new("RGBA", (padded_size, padded_size), (15, 23, 42, 255))  # slate-900
inner_img = img.resize((inner, inner), Image.LANCZOS)
bg.paste(inner_img, (pad, pad), inner_img)
bg.save(f"{out_dir}/icon-512-maskable.png")
print("Icons generated.")
```

Run with: `python scripts/generate_icons.py` (requires Pillow: `pip install Pillow`)

### 3. `app/layout.tsx` — Add PWA meta tags

In the `<head>` section (inside `metadata` export or directly in `<head>`):

```typescript
// In the metadata export:
export const metadata: Metadata = {
  // ... existing metadata
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'Abu Oracle',
  },
  formatDetection: { telephone: false },
};
```

Also add directly in the `<head>` JSX if not using the metadata API:
```html
<link rel="manifest" href="/manifest.json" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="Abu Oracle" />
<link rel="apple-touch-icon" href="/icons/icon-192.png" />
<meta name="theme-color" content="#f59e0b" />
```

### 4. `next.config.js` — Correct MIME type for manifest

Next.js serves static files from `public/` automatically, but some reverse proxies
(including the Cloudflare Worker) may strip the Content-Type. Add:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // ... existing config
  async headers() {
    return [
      {
        source: '/manifest.json',
        headers: [{ key: 'Content-Type', value: 'application/manifest+json' }],
      },
    ];
  },
};
```

### 5. Service Worker (optional — only if Codex has capacity)

If implementing a service worker, use **Next.js App Router pattern** (no `next-pwa` package needed):

```typescript
// next_app/public/sw.js — minimal cache-first for static assets
const CACHE = 'abu-oracle-v1';
const STATIC = ['/', '/chart', '/manifest.json', '/icons/icon-192.png'];

self.addEventListener('install', e =>
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)))
);
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
```

Register in `app/layout.tsx`:
```typescript
// Client component or useEffect:
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
```

**Note**: Service worker is optional for this spec. PWA installability only requires
manifest.json + HTTPS + the meta tags. Service worker enhances offline support but
is not required for "Add to Home Screen" on modern browsers.

## Acceptance criteria

- [ ] `next_app/public/manifest.json` exists with correct JSON and colors
- [ ] `next_app/public/icons/icon-192.png` and `icon-512.png` exist (any valid PNG, even a placeholder)
- [ ] `next_app/app/layout.tsx` includes `<link rel="manifest">` and apple meta tags
- [ ] `npx tsc --noEmit` passes
- [ ] Lighthouse PWA audit: "Installable" criterion passes (can be verified locally with Chrome DevTools)
- [ ] NO new npm dependencies introduced (no `next-pwa`)

## Out of scope

- Push notifications (future — TEL-C01 + backend changes needed)
- Full offline mode (chart data fetches require the backend)
- App store submission (out of scope for this sprint)
