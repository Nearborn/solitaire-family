"""Run with `python -m unittest discover -s tests` after installing pygame-ce.
The games are also tested without pygame when executing this file directly.
"""
import importlib.util
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if 'game' not in sys.modules:
    pkg = types.ModuleType('game')
    pkg.__path__ = [str(ROOT / 'game')]
    sys.modules['game'] = pkg
for name in ('cards', 'rules', 'extra_games'):
    fq = 'game.' + name
    if fq not in sys.modules:
        spec = importlib.util.spec_from_file_location(fq, ROOT / 'game' / (name + '.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[fq] = mod
        spec.loader.exec_module(mod)

from game.extra_games import ExtraGame, Card
from game.rules import VARIANTS, ADDITIONAL_GAMES


class RulesTests(unittest.TestCase):
    def test_original_six_unchanged(self):
        self.assertEqual([v.short_name for v in VARIANTS[:6]],
                         ['Klondike', 'Draw Three', 'Yukon', 'Spider', 'Spider', 'Spider'])

    def test_card_conservation(self):
        for name in ADDITIONAL_GAMES:
            with self.subTest(name=name):
                m = ExtraGame(name, seed=4)
                self.assertEqual(m.card_count(), 48 if m.is_grid else 52)
                self.assertEqual(len(m.foundations), 4)
                if m.is_penguin:
                    self.assertEqual(sorted(map(len, m.tableau)), [7]*7)
                if m.is_freecell:
                    self.assertEqual(sorted(map(len, m.tableau)), [6]*4 + [7]*4)
                if m.is_tommy:
                    self.assertEqual(len(m.tableau), 8)

    def test_australian_stock_and_undo(self):
        m = ExtraGame('Australian Patience', 22)
        self.assertEqual(len(m.stock), 24)
        for _ in range(24):
            self.assertTrue(m.draw())
        self.assertFalse(m.draw())
        self.assertEqual(len(m.waste), 24)
        self.assertEqual(m.card_count(), 52)
        self.assertTrue(m.undo())
        self.assertEqual(len(m.waste), 23)
        self.assertEqual(len(m.stock), 1)

    def test_sir_tommy_pending_restrictions(self):
        m = ExtraGame('Old Patience / Sir Tommy', 7)
        self.assertTrue(m.draw())
        self.assertFalse(m.draw())
        self.assertTrue(m.move(('p', 0, 0), ('t', 0, 0)))
        self.assertIsNone(m.pending)
        self.assertFalse(m.move(('t', 0, 0), ('t', 1, 0)))
        self.assertTrue(m.undo())
        self.assertIsNotNone(m.pending)
        self.assertEqual(m.card_count(), 52)

    def test_freecell_empty_cell_and_undo(self):
        m = ExtraGame('FreeCell', 5)
        top = len(m.tableau[0]) - 1
        c = m.tableau[0][-1]
        self.assertTrue(m.move(('t', 0, top), ('c', 0, 0)))
        self.assertEqual(m.cells[0], c)
        self.assertTrue(m.undo())
        self.assertIsNone(m.cells[0])
        self.assertEqual(m.tableau[0][-1], c)

    def test_penguin_beak_setup(self):
        m = ExtraGame('Penguin', 5)
        self.assertEqual(sum(map(len, m.foundations)), 3)
        self.assertTrue(all(pile[0].rank == m.beak_rank for pile in m.foundations if pile))
        self.assertEqual(m.card_count(), 52)

    def test_grid_gaps(self):
        for name in ('Addiction Solitaire', 'Maze Solitaire'):
            m = ExtraGame(name, 9)
            self.assertEqual(len(m.grid), 52 if m.is_addiction else 54)
            self.assertEqual(sum(c is None for c in m.grid), 4 if m.is_addiction else 6)
            self.assertEqual(m.card_count(), 48)
            for gap in [i for i, c in enumerate(m.grid) if c is None]:
                self.assertFalse(m._can_fill_gap(Card(13, 0), gap) if m.is_addiction else
                                 m._can_fill_gap(Card(13, 0), gap))



# Extended coverage (also works without pygame/Juno).
class RegressionTests(unittest.TestCase):
    def test_each_grid_opens_with_a_move_and_undo_works(self):
        for name in ('Addiction Solitaire', 'Maze Solitaire'):
            for seed in range(100):
                with self.subTest(name=name, seed=seed):
                    game = ExtraGame(name, seed)
                    moves = game.grid_legal_moves()
                    self.assertTrue(moves)
                    before = game.grid[:]
                    a, b = moves[0]
                    self.assertTrue(game.move(('g', a, 0), ('g', b, 0)))
                    self.assertEqual(game.card_count(), 48)
                    self.assertTrue(game.undo())
                    self.assertEqual(game.grid, before)

    def test_sir_tommy_foundation_ignores_suit_not_rank(self):
        game = ExtraGame('Old Patience / Sir Tommy', 8)
        game.tableau = [[Card(1, 1)], [Card(2, 2)], [Card(4, 3)]] + [[] for _ in range(5)]
        game.foundations = [[] for _ in range(4)]
        self.assertTrue(game.move(('t', 0, 0), ('f', 0, 0)))
        self.assertTrue(game.move(('t', 1, 0), ('f', 0, 0)))
        self.assertFalse(game.move(('t', 2, 0), ('f', 0, 0)))
        self.assertEqual([c.rank for c in game.foundations[0]], [1, 2])

    def test_addiction_stuck_then_three_reshuffles(self):
        game = ExtraGame('Addiction Solitaire', 13)
        while game.has_grid_move() and not game.is_won():
            src, dst = game.grid_legal_moves()[0]
            self.assertTrue(game.move(('g', src, 0), ('g', dst, 0)))
        if not game.is_won():
            self.assertTrue(game.reshuffle())
            self.assertEqual(game.reshuffles, 2)
            self.assertEqual(game.card_count(), 48)
            self.assertTrue(game.undo())
            self.assertEqual(game.reshuffles, 3)

    def test_four_quick_rules_for_each_game(self):
        from game.quick_rules import QUICK_RULES
        for name in [variant.name for variant in VARIANTS] + list(ADDITIONAL_GAMES):
            with self.subTest(name=name):
                self.assertEqual(len(QUICK_RULES[name]), 4)

if __name__ == "__main__":
    unittest.main()
