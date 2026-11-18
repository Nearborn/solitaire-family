"""v1.3 regression suite: new games, FreeCell legality and card conservation.

Run without pygame, Juno or external packages.
"""
import sys
import types
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if 'game' not in sys.modules:
    pkg = types.ModuleType('game')
    pkg.__path__ = [str(ROOT / 'game')]
    sys.modules['game'] = pkg

from game.cards import SUITS
from game.extra_games import Card, ExtraGame
from game.novel_games import NovelGame, NOVEL_GAMES
from game.quick_rules import QUICK_RULES
from game.rules import VARIANTS, SPECIAL_VARIANTS, GARGANTUA, BEETLE
from game.table import Table, deal_from_stock, recycle_waste, STOCK, WASTE


class V130Rules(unittest.TestCase):
    def test_registry_all_24(self):
        names = [v.name for v in VARIANTS + SPECIAL_VARIANTS]
        self.assertEqual(len(names), 24)
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(set(NOVEL_GAMES).issubset(names))
        for name in names:
            self.assertEqual(len(QUICK_RULES[name]), 4)

    def test_freecell_valid_2_block_invalid_3(self):
        g = ExtraGame('FreeCell', 1)
        g.cells = [Card(7, 3), Card(7, 1), None, Card(6, 2)]
        g.tableau = [[Card(11, 1), Card(10, 0), Card(9, 2)],
                     [Card(12, 0)]] + [[Card(5, i % 4)] for i in range(6)]
        self.assertEqual(g.supermove_capacity(0, 1), 2)
        self.assertFalse(g.move(('t', 0, 0), ('t', 1, 0)))
        self.assertIn('only 2 movable', g.message)
        g.tableau[1][-1] = Card(11, 2)  # two-card tail starts at 10 spades
        self.assertTrue(g.move(('t', 0, 1), ('t', 1, 0)))
        self.assertEqual(len(g.tableau[1]), 3)
        self.assertTrue(g.undo())
        g.tableau[1][-1] = Card(12, 0)
        g.tableau[2] = []
        self.assertEqual(g.supermove_capacity(0, 1), 4)
        self.assertTrue(g.move(('t', 0, 0), ('t', 1, 0)))
        self.assertTrue(g.undo())
        # An EMPTY destination is consumed, not available as workspace.
        g.tableau[1] = []
        self.assertEqual(g.supermove_capacity(0, 1), 4)  # column 2 still free

    def test_classic_two_deck_counts_and_redeal(self):
        table = Table(GARGANTUA)
        self.assertEqual([len(p) for p in table.columns], list(range(1, 10)))
        self.assertEqual(len(table.stock), 59)
        self.assertEqual(len(table.foundations), 8)
        self.assertEqual(sum(map(len, table.columns)) + len(table.stock), 104)
        for _ in range(59):
            table.do(deal_from_stock(table))
        first = table.waste[0]
        table.do(recycle_waste(table))
        self.assertIs(table.stock[-1], first)
        for _ in range(59):
            table.do(deal_from_stock(table))
        self.assertIsNone(recycle_waste(table))
        for _ in range(59):
            self.assertTrue(table.undo())
        self.assertTrue(table.undo())  # Undo recycle -> pass is available again
        self.assertIsNotNone(recycle_waste(table))

        table = Table(BEETLE)
        self.assertEqual(list(map(len, table.columns)), [5]*4 + [4]*6)
        self.assertEqual(len(table.stock), 60)
        self.assertTrue(all(c.face_up for pile in table.columns for c in pile))
        self.assertEqual(len(table.foundations), 8)
        for _ in range(6):
            self.assertIsNotNone(deal_from_stock(table))
            table.do(deal_from_stock(table))
        self.assertFalse(table.stock)
        self.assertTrue(all(len(pile) == (11 if i < 4 else 10)
                            for i, pile in enumerate(table.columns)))

    def test_deal_sizes_and_conservation(self):
        for name in NOVEL_GAMES:
            for seed in range(20):
                with self.subTest(name=name, seed=seed):
                    g = NovelGame(name, seed)
                    size = 104 if name == 'Zodiac' else 52
                    self.assertEqual(g.card_count(), size)
                    self.assertFalse(g.is_won())
                    if name == 'Black Hole':
                        self.assertEqual(list(map(len,g.tableau)), [3]*17)
                        self.assertEqual(g.foundations[0], [Card(1,0)])
                    if name == 'Beleaguered Castle':
                        self.assertEqual(list(map(len,g.tableau)), [6]*8)
                        self.assertEqual([p[0] for p in g.foundations],
                                         [Card(1,i) for i in range(4)])
                    if name == 'Zodiac':
                        self.assertEqual(len(g.tableau), 24)
                        self.assertEqual(len(g.cells), 8)
                        self.assertEqual(len(g.stock), 72)
                    if name == 'Birthday':
                        self.assertEqual(len(g.stock), 48)
                        self.assertEqual([p[0].rank for p in g.foundations],
                                         [2,10,6,7])

    def test_blackhole_wrap_and_undo(self):
        g = NovelGame('Black Hole', 6)
        # Exchange a 3rd-place card with a King to keep exact deck inventory.
        target = Card(13, 2)
        owner = next(i for i,p in enumerate(g.tableau) if target in p)
        j = g.tableau[owner].index(target)
        g.tableau[owner][j], g.tableau[0][-1] = g.tableau[0][-1], target
        before = g._snapshot()
        self.assertTrue(g.move(('t', 0, 2), ('f', 0, 0)))
        self.assertEqual(g.foundations[0][-1].rank, 13)
        self.assertEqual(g.card_count(), 52)
        self.assertTrue(g.undo())
        self.assertEqual(g._snapshot(), before)
        g.tableau[0][-1] = Card(3, 0)
        self.assertFalse(g.move(('t', 0, 2), ('f', 0, 0)))

    def test_castle_one_card_only_any_suit_tableau(self):
        g = NovelGame('Beleaguered Castle', 5)
        g.tableau[0][-1] = Card(6, 2)
        g.tableau[1][-1] = Card(7, 1)
        before = g._snapshot()
        self.assertFalse(g.move(('t', 0, 1), ('t', 1, 0)))
        before = g._snapshot()
        self.assertTrue(g.move(('t', 0, 5), ('t', 1, 0)))
        self.assertEqual(g.tableau[1][-1], Card(6,2))
        self.assertTrue(g.undo())
        self.assertEqual(g._snapshot(), before)

    def test_birthday_four_passes_and_wrap(self):
        g = NovelGame('Birthday', 5)
        self.assertEqual(g.birthday_target, '1956')
        card = Card(11, 1)  # Q? suit 1 starts at 10, needs 11 = Jack
        g.stock.remove(card)
        g.waste.append(card)
        self.assertTrue(g.move(('w', 0, 0), ('f', 1, 0)))
        self.assertEqual(g.foundations[1][-1], card)
        self.assertTrue(g.undo())
        g = NovelGame('Birthday', 2)
        for pass_no in range(4):
            while g.stock:
                self.assertTrue(g.draw())
            if pass_no < 3:
                self.assertTrue(g.draw())
                self.assertEqual(g.passes, pass_no + 2)
        self.assertFalse(g.draw())
        self.assertEqual(g.card_count(), 52)
        self.assertTrue(g.undo())
        self.assertTrue(g.draw())
        self.assertRaises(ValueError, NovelGame, 'Birthday', 1, '2000')

    def test_zodiac_phase_and_undo(self):
        g = NovelGame('Zodiac', 14)
        g.draw()
        self.assertFalse(g.move(('w',0,0),('f',0,0)))
        self.assertIn('unlock', g.message)
        # Find any legal phase-one Equator/Zodiac placement.
        legal = [(i,j) for i,c in enumerate(g.cells)
                 for j,p in enumerate(g.tableau)
                 if abs(c.rank-p[-1].rank)==1 and c.suit==p[-1].suit]
        self.assertTrue(legal)
        i,j = legal[0]
        previous = g._snapshot()
        self.assertTrue(g.move(('c',i,0),('t',j,0)))
        self.assertEqual(g.card_count(),104)
        self.assertTrue(g.undo())
        self.assertEqual(previous,g._snapshot())
        # Packing every remaining stock/waste card simulates the end of phase 1.
        while g.waste:
            g.tableau[0].append(g.waste.pop())
        while g.stock:
            g.tableau[0].append(g.stock.pop())
        self.assertTrue(g.phase_two)
        self.assertFalse(g.move(('c',0,0),('t',0,0)))
        self.assertEqual(g.card_count(),104)
        # Aces and Kings occupy separate suit foundations.
        self.assertTrue(all(not p for p in g.foundations))

    def test_undo_all_novel_draws(self):
        for name in ('Birthday','Zodiac'):
            g = NovelGame(name, 17)
            before = g._snapshot()
            self.assertTrue(g.draw())
            self.assertTrue(g.undo())
            self.assertEqual(g._snapshot(), before)


if __name__ == '__main__':
    unittest.main()
