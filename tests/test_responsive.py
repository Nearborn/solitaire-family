"""Screen-rotation regression tests for the packaged Solitaire game.

Run with: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests -v
"""
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from game import SolitaireGame


class DisplayResizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_classic_board_survives_portrait_to_landscape(self):
        screen = pygame.display.set_mode((430, 932))
        game = SolitaireGame(screen)
        original_table = game.table
        original_variant = game.current_variant
        original_cards = tuple(id(card) for pile in game.table.columns for card in pile)
        for size in ((932, 430), (1180, 820), (932, 430)):
            screen = pygame.display.set_mode(size)
            game.resize_display(screen)
            self.assertEqual((game.layout.width, game.layout.height), size)
            self.assertIs(game.table, original_table)
            self.assertIs(game.current_variant, original_variant)
            self.assertEqual(tuple(id(c) for pile in game.table.columns for c in pile),
                             original_cards)
            game.draw()
            pygame.display.flip()

    def test_special_board_preserves_model_and_shuffle_count(self):
        screen = pygame.display.set_mode((960, 540))
        game = SolitaireGame(screen)
        addiction = next(v for v in game.variants if v.name == "Addiction Solitaire")
        game.new_game(addiction)
        original_special = game.special
        original_model = game.special.model
        remaining = original_model.reshuffles
        for size in ((844, 390), (1200, 800)):
            screen = pygame.display.set_mode(size)
            game.resize_display(screen)
            self.assertIs(game.special, original_special)
            self.assertIs(game.special.model, original_model)
            self.assertEqual(game.special.model.reshuffles, remaining)
            self.assertEqual((game.layout.width, game.layout.height), size)
            game.draw()
            pygame.display.flip()


if __name__ == "__main__":
    unittest.main()
