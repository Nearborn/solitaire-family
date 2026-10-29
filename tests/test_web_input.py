"""Regression tests for browser mouse/touch dispatch and coordinate mapping."""
import json
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import main as web_main
from game import SolitaireGame


class BrowserInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def dispatch(self, game, points):
        width, height = game.screen.get_size()
        commands = [
            {"type": kind, "x": x / width, "y": y / height, "button": 0}
            for kind, (x, y) in points
        ]

        class FakeBrowser:
            solitairePointerReady = True
            def solitaireDrainInput(self):
                return json.dumps(commands)

        with patch.object(web_main, "WEB", True), patch.object(
                web_main, "window", FakeBrowser(), create=True):
            events = web_main.browser_pointer_events(game.screen)
        self.assertEqual(len(events), len(commands))
        for e in events:
            game.handle_event(e)
        return events

    def test_rules_button_receives_web_click(self):
        screen = pygame.display.set_mode((960, 540))
        game = SolitaireGame(screen)
        game.deal = None
        game.state = "playing"
        p = game.layout.rules_button.center
        events = self.dispatch(game, [("down", p), ("up", p)])
        self.assertEqual(events[0].type, pygame.MOUSEBUTTONDOWN)
        self.assertEqual(events[0].pos, p)
        self.assertEqual(events[1].type, pygame.MOUSEBUTTONUP)
        self.assertTrue(game.rules_open)

    def test_web_drag_starts_and_tracks_touch(self):
        screen = pygame.display.set_mode((940, 440))
        game = SolitaireGame(screen)
        game.deal = None
        game.state = "playing"
        cards = game.table.columns[0]
        x = game.layout.column_left(0) + game.layout.card_width // 3
        y = game.layout.fan_offsets(cards)[-1] + game.layout.card_height // 3
        self.dispatch(game, [("down", (x, y)), ("move", (x + 70, y + 30))])
        self.assertTrue(game.drag.holding)
        self.assertTrue(game.drag.moved)
        self.assertNotEqual(game.drag.position, game.drag.home)


if __name__ == "__main__":
    unittest.main()
