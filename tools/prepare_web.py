"""Prepare Pygbag output as a responsive, installable phone/tablet web app."""
import json
import re
import sys
from pathlib import Path
from shutil import copyfile

root = Path(__file__).resolve().parent.parent
web = Path(sys.argv[1]).resolve()
index = web / "index.html"
if not index.is_file():
    raise SystemExit(f"No Pygbag index.html at {index}")

for name in ("favicon.png", "icon-192.png", "icon-512.png"):
    copyfile(root / name, web / name)

manifest = {
    "name": "Solitaire Collection — 18 Games",
    "short_name": "Solitaire",
    "id": "./", "start_url": "./index.html", "scope": "./",
    "display": "standalone", "orientation": "landscape",
    "theme_color": "#1e5c44", "background_color": "#1e5c44",
    "icons": [
        {"src": "./icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "./icon-512.png", "sizes": "512x512", "type": "image/png"},
    ],
}
(web / "manifest.webmanifest").write_text(json.dumps(manifest), encoding="utf-8")
copyfile(root / "tools" / "pointer_bridge.js", web / "pointer_bridge.js")

html = index.read_text(encoding="utf-8")
if "</head>" not in html or "</body>" not in html:
    raise SystemExit("Unexpected Pygbag HTML template")
# Remove any conflicting Pygbag default viewport declaration.
html = re.sub(r'<meta\s+name=["\']viewport["\'][^>]*>', '', html, flags=re.I)
head = """<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=contain,user-scalable=no">
<meta name="theme-color" content="#1e5c44">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="manifest" href="./manifest.webmanifest">
<link rel="icon" href="./favicon.png">
<style id="solitaire-viewport-css">
/* Pygbag's default CSS caps the portrait-sized canvas but never enlarges it.
   Fill the browser viewport instead. Python resizes the actual framebuffer. */
html, body {
  margin: 0 !important; padding: 0 !important;
  width: 100% !important; height: 100% !important;
  overflow: hidden !important;
  background: #1e5c44 !important;
  overscroll-behavior: none; touch-action: none;
}
canvas#canvas {
  position: fixed !important; left: 0 !important; top: 0 !important;
  display: block !important; z-index: 10 !important;
  width: 100vw !important;
  height: 100vh !important; height: 100dvh !important;
  max-width: none !important; max-height: none !important;
  min-width: 0 !important; min-height: 0 !important;
  margin: 0 !important; padding: 0 !important;
  object-fit: fill !important; touch-action: none !important;
  pointer-events: auto !important;
}
#rotate-msg {
  display: none; position: fixed; inset: 0; z-index: 2147483647;
  background: #123b2c; color: white; box-sizing: border-box;
  font: 600 20px system-ui, sans-serif;
  align-items: center; justify-content: center; text-align: center;
  padding: 30px;
}
@media (orientation: portrait) and (pointer: coarse) {
  #rotate-msg { display: flex; }
}
</style>"""
body = """<div id="rotate-msg">Rotate your phone sideways to play Solitaire.</div>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('./sw.js').catch(console.warn);
  });
}
</script>"""
if 'id="solitaire-viewport-css"' not in html:
    html = html.replace("</head>", head + "\n</head>", 1)
if 'id="rotate-msg"' not in html:
    html = html.replace("</body>", body + "\n</body>", 1)
# Pointer bridge runs on the actual SDL canvas, never the unused 3D canvas.
# It also maps CSS coordinates to Pygame logical pixels in main.py.
html = html.replace("</body>", '<script src="./pointer_bridge.js" defer></script>\\n</body>', 1)
index.write_text(html, encoding="utf-8")

precache = ["./" + p.name for p in web.iterdir()
            if p.is_file() and p.suffix.lower() in
            (".html", ".js", ".wasm", ".data", ".apk", ".zip", ".png", ".webmanifest")]
worker = """const CACHE = 'solitaire-v1.4.1';
const FILES = __FILES__;
self.addEventListener('install', event => event.waitUntil((async () => {
  const cache = await caches.open(CACHE);
  await Promise.allSettled(FILES.map(url => cache.add(url)));
  await self.skipWaiting();
})()));
self.addEventListener('activate', event => event.waitUntil((async () => {
  const keys = await caches.keys();
  await Promise.all(keys.filter(k => k.startsWith('solitaire-') && k !== CACHE)
                         .map(k => caches.delete(k)));
  await self.clients.claim();
})()));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(event.request);
    if (cached && event.request.mode !== 'navigate') return cached;
    try {
      const response = await fetch(event.request);
      if (response.ok) cache.put(event.request, response.clone());
      return response;
    } catch (error) {
      if (cached) return cached;
      throw error;
    }
  })());
});
""".replace("__FILES__", json.dumps(sorted(precache)))
(web / "sw.js").write_text(worker, encoding="utf-8")
(web / ".nojekyll").touch()
print(f"Prepared {len(precache)} web assets in {web}")
