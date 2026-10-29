"""End-to-end WebAssembly smoke test using headless Chrome.

Run after Pygbag builds web assets and before publishing them.
"""
import hashlib
import http.server
import os
import shutil
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path("build/web").resolve()


def main():
    if not (ROOT / "index.html").exists():
        raise RuntimeError("Pygbag build/web/index.html is missing")

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)
        def log_message(self, fmt, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/?smoketest=1"
    try:
        with sync_playwright() as pw:
            chrome = (shutil.which("google-chrome") or
                      shutil.which("google-chrome-stable") or
                      shutil.which("chromium"))
            browser = pw.chromium.launch(
                executable_path=chrome if chrome else None,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage",
                      "--autoplay-policy=no-user-gesture-required"],
            )
            page = browser.new_page(viewport={"width": 960, "height": 540})
            page.on("pageerror", lambda e: print("Browser JS error:", str(e)))
            print("Opening", url)
            page.goto(url, wait_until="domcontentloaded", timeout=50000)
            page.wait_for_function("window.solitairePointerReady === true", timeout=45000)
            size = page.locator("#canvas").bounding_box()
            print("Canvas bounds:", size)
            assert size and size["width"] >= 920 and size["height"] >= 500, size
            # Pygbag may wait for the first user gesture to enable audio.
            page.mouse.click(480, 270)
            time.sleep(5)
            canvas = page.locator("#canvas")

            def digest():
                return hashlib.sha256(canvas.screenshot(timeout=20000)).hexdigest()

            previous = digest()
            stable = False
            for _ in range(22):
                time.sleep(0.6)
                current = digest()
                if current == previous:
                    stable = True
                    break
                previous = current
            print("Canvas became stationary:", stable)
            before = digest()
            # Rules button centre for 960x540 using Layout._buttons (web band 78).
            page.mouse.click(629, 38)
            time.sleep(0.8)
            after = digest()
            print("Rules click changed canvas:", before != after)
            assert before != after, (
                "Browser input failed: tapping Rules did not change rendered game."
                " Check JavaScript console and event bridge.")
            print("Actual WebAssembly browser click smoke test passed.")
            # A true full reload must get a new deck seed, not the deterministic
            # WebAssembly random state from the previous browser page.
            page.wait_for_function(
                "typeof window.solitaireLastDealSeed === 'string' && "
                "window.solitaireLastDealSeed.length === 32",
                timeout=45000
            )
            previous_seed = page.evaluate("window.solitaireLastDealSeed")
            page.reload(wait_until="domcontentloaded", timeout=50000)
            page.wait_for_function(
                "typeof window.solitaireLastDealSeed === 'string' && "
                "window.solitaireLastDealSeed.length === 32",
                timeout=45000
            )
            current_seed = page.evaluate("window.solitaireLastDealSeed")
            print("Deal seeds are distinct after reload:", previous_seed != current_seed)
            assert current_seed != previous_seed, (
                "WebAssembly game reuses the same shuffle seed after page reload"
            )
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
