"""Regression tests: distinct browser entropy for each reload and deal.

The browser uses crypto.getRandomValues rather than relying on Python-WASM's
implicit random initialization.
"""
import sys
import types
import unittest
from unittest.mock import patch

from game import entropy
from game.table import Table
from game.extra_games import ExtraGame
from game.more_games import MoreGame


class BrowserRandomTests(unittest.TestCase):

    def test_browser_crypto_generates_distinct_seeds(self):
        class Browser:
            def __init__(self):
                self.calls = 0
                self.solitaireLastDealSeed = None

            def solitaireDealSeed(self):
                self.calls += 1
                return f"{self.calls:032x}"

        browser = Browser()
        with patch.object(sys, "platform", "emscripten"), patch.dict(
                sys.modules, {"platform": types.SimpleNamespace(window=browser)}):
            self.assertEqual(entropy.fresh_seed(), 1)
            self.assertEqual(entropy.fresh_seed(), 2)
            self.assertEqual(browser.solitaireLastDealSeed, f"{2:032x}")

            standard = Table()
            first = tuple((c.suit, c.rank) for c in standard.stock)
            standard.new_deal()
            second = tuple((c.suit, c.rank) for c in standard.stock)
            self.assertNotEqual(first, second)

            extra_one = ExtraGame("FreeCell")
            extra_two = ExtraGame("FreeCell")
            self.assertNotEqual(extra_one.rng.getstate(),
                                extra_two.rng.getstate())

            more_one = MoreGame("Golf")
            more_two = MoreGame("Golf")
            self.assertNotEqual(more_one.rng.getstate(),
                                more_two.rng.getstate())

        self.assertEqual(browser.calls, 8)

    def test_explicit_seed_still_reproduces_deals(self):
        import random
        left = Table(rng=random.Random(1234))
        right = Table(rng=random.Random(1234))
        self.assertEqual(
            [(c.suit, c.rank) for c in left.stock],
            [(c.suit, c.rank) for c in right.stock],
        )
        a = ExtraGame("FreeCell", seed=42)
        b = ExtraGame("FreeCell", seed=42)
        self.assertEqual(a.tableau, b.tableau)
        self.assertEqual(
            MoreGame("Golf", seed=42).rng.getstate(),
            MoreGame("Golf", seed=42).rng.getstate()
        )


if __name__ == "__main__":
    unittest.main()
