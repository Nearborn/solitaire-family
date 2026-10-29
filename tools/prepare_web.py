"""Prepare Pygbag's web output for phone/tablet installation."""
import json
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
    "name": "Solitaire Collection — 18 Games", "short_name": "Solitaire",
    "id": "./", "start_url": "./index.html", "scope": "./",
    "display": "standalone", "orientation": "landscape",
    "theme_color": "#1e5c44", "background_color": "#1e5c44",
    "icons": [{"src": "./icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "./icon-512.png", "sizes": "512x512", "type": "image/png"}],
}
(web / "manifest.webmanifest").write_text(json.dumps(manifest), encoding="utf-8")
html = index.read_text(encoding="utf-8")
head = """<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="theme-color" content="#1e5c44">
<link rel="manifest" href="./manifest.webmanifest">
<link rel="icon" href="./favicon.png">
<style>
html,body{margin:0;padding:0;overflow:hidden;background:#1e5c44;touch-action:none}
canvas{max-width:100vw;max-height:100dvh;object-fit:contain;touch-action:none}
#rotate-msg{display:none;position:fixed;inset:0;z-index:99999;background:#123b2c;color:white;
font:600 20px system-ui;align-items:center;justify-content:center;text-align:center;padding:30px}
@media(orientation:portrait) and (max-width:600px){#rotate-msg{display:flex}}
</style>"""
body = """<div id="rotate-msg">Rotate your phone sideways to play Solitaire.</div>
<script>
if('serviceWorker' in navigator){
window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(console.warn));
}
</script>"""
if 'id="rotate-msg"' not in html:
    if '</head>' not in html or '</body>' not in html:
        raise SystemExit("Unexpected Pygbag HTML template")
    html=html.replace('</head>',head+'\n</head>',1).replace('</body>',body+'\n</body>',1)
    index.write_text(html,encoding='utf-8')
precache = ["./"+p.name for p in web.iterdir() if p.is_file() and p.suffix.lower() in
           (".html",".js",".wasm",".data",".apk",".zip",".png",".webmanifest")]
worker = """const CACHE='solitaire-v1.3.2';
const FILES=__FILES__;
self.addEventListener('install',e=>e.waitUntil((async()=>{
const c=await caches.open(CACHE);await Promise.allSettled(FILES.map(x=>c.add(x)));
await self.skipWaiting()})()));
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch',e=>{
if(e.request.method!=='GET')return;
e.respondWith((async()=>{const c=await caches.open(CACHE);
const hit=await c.match(e.request);
if(hit&&e.request.mode!=='navigate')return hit;
try{const r=await fetch(e.request);if(r.ok)c.put(e.request,r.clone());return r}
catch(err){if(hit)return hit;throw err}})())});
""".replace("__FILES__",json.dumps(sorted(precache)))
(web / "sw.js").write_text(worker,encoding="utf-8")
(web / ".nojekyll").touch()
print(f"Prepared {len(precache)} web assets in {web}")
