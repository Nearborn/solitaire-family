"""Integration regression for Juno 24-game suite in the web Pygame frontend."""
import os
import unittest
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
from game import SolitaireGame
from game.novel_games import NOVEL_GAMES
from game.more_games import MORE_GAMES


class WebTwentyFour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_registers_every_variant(self):
        screen = pygame.display.set_mode((960, 540))
        game = SolitaireGame(screen)
        self.assertEqual(len(game.variants), 24)
        self.assertEqual(len({v.name for v in game.variants}), 24)
        for name in ("Black Hole", "Zodiac", "Gargantua", "Beetle", "Birthday", "Beleaguered Castle"):
            self.assertIn(name, {v.name for v in game.variants})

    def test_all_variants_paint_and_keep_state_after_web_rotation(self):
        screen = pygame.display.set_mode((980, 540))
        game = SolitaireGame(screen)
        for variant in game.variants:
            with self.subTest(name=variant.name):
                game.new_game(variant)
                game.draw()
                pygame.display.flip()
                model = game.special.model if game.special is not None else game.table
                for size in ((844,390),(1180,820)):
                    screen = pygame.display.set_mode(size)
                    game.resize_display(screen)
                    self.assertIs(game.special.model if game.special is not None else game.table, model)
                    game.draw()
                    pygame.display.flip()
                    self.assertEqual(game.layout.width, size[0])
                    self.assertEqual(game.layout.height, size[1])
                screen = pygame.display.set_mode((980,540))
                game.resize_display(screen)

    def test_variant_picker_contains_twenty_four_click_targets(self):
        screen = pygame.display.set_mode((844, 390))
        game = SolitaireGame(screen)
        game.picker_open = True
        game.draw()
        self.assertEqual(len(game.layout.picker_rows(24)), 24)
        for i,rect in enumerate(game.layout.picker_rows(24)):
            self.assertEqual(game.layout.picker_row_at(rect.center,24),i)
            self.assertTrue(screen.get_rect().colliderect(rect))


if __name__ == '__main__':
    unittest.main()
