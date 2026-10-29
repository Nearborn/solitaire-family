"""Independent, explicit deck seeds for desktop Python and browser WebAssembly.

The browser's virtual OS may not supply fresh entropy to random.Random(None),
so never rely on implicit seeding in a WebAssembly session.
"""
import random
import secrets
import sys
import time

_counter = 0


def fresh_seed():
    """Return a 128-bit seed; browser uses Web Crypto, desktop uses system entropy."""
    global _counter
    _counter += 1

    if sys.platform == "emscripten":
        try:
            from platform import window
            # Installed by tools/prepare_web.py in the HTML page.
            raw = str(window.solitaireDealSeed())
            if len(raw) != 32 or any(c not in "0123456789abcdefABCDEF" for c in raw):
                raise ValueError("Browser seed is not 128-bit hexadecimal")
            value = int(raw, 16)
            # Also expose for browser-level regression tests (not gameplay).
            window.solitaireLastDealSeed = str(raw)
            return value
        except Exception as exc:
            # Never fall back to a fixed seed. This branch is only defensive;
            # the production HTML supplies crypto.getRandomValues.
            print("Web Crypto seed unavailable:", exc)
            return ((time.time_ns() << 32) ^ (_counter * 0x9E3779B97F4A7C15))

    return secrets.randbits(128)


def fresh_rng():
    """A separate random generator for every independent shuffled deal."""
    return random.Random(fresh_seed())
