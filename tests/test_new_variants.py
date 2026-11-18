"""Model invariants for all six v1.2 additions (runs with stdlib only)."""
import unittest
import sys
import types
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if 'game' not in sys.modules:
    pkg = types.ModuleType('game')
    pkg.__path__ = [str(ROOT / 'game')]
    sys.modules['game'] = pkg
from game.extra_games import ExtraGame, Card
from game.more_games import MoreGame, MORE_GAMES
from game.rules import SPECIAL_VARIANTS, ADDITIONAL_GAMES, VARIANTS
from game.quick_rules import QUICK_RULES


class Additions(unittest.TestCase):
    def test_menu_and_original_registry(self):
        self.assertEqual(len(VARIANTS), 8)
        self.assertEqual(len(ADDITIONAL_GAMES), 6)
        self.assertEqual(len(SPECIAL_VARIANTS), 16)
        self.assertEqual(len(VARIANTS)+len(SPECIAL_VARIANTS), 24)
        for game in VARIANTS + SPECIAL_VARIANTS:
            self.assertIn(game.name, QUICK_RULES)
            self.assertEqual(len(QUICK_RULES[game.name]), 4)

    def test_australian_recycle_once_and_undo(self):
        m = ExtraGame('Australian Patience (One Redeal)', 11)
        self.assertEqual(m.redeals_remaining, 1)
        self.assertEqual(m.card_count(), 52)
        first_order = []
        for _ in range(24):
            first_order.append(m.stock[-1])
            self.assertTrue(m.draw())
        self.assertEqual(m.stock, [])
        self.assertTrue(m.draw())
        self.assertEqual(m.redeals_remaining, 0)
        self.assertEqual(m.waste, [])
        self.assertEqual(m.stock[-1], first_order[0])
        self.assertTrue(m.undo())
        self.assertEqual(m.redeals_remaining, 1)
        self.assertEqual(m.waste, first_order)
        self.assertTrue(m.draw())  # spend the single redeal again
        for _ in range(24):
            self.assertTrue(m.draw())
        self.assertFalse(m.draw())
        self.assertEqual(m.card_count(), 52)
        old = ExtraGame('Australian Patience', 11)
        for _ in range(24): self.assertTrue(old.draw())
        self.assertFalse(old.draw())

    def test_eight_off_deal_and_move(self):
        m = ExtraGame('Eight Off', 23)
        self.assertEqual(list(map(len, m.tableau)), [6]*8)
        self.assertEqual(len(m.cells), 8)
        self.assertEqual(sum(c is not None for c in m.cells), 4)
        self.assertEqual(m.card_count(), 52)
        i = len(m.tableau[0])-1
        card = m.tableau[0][-1]
        self.assertTrue(m.move(('t',0,i),('c',4,0)))
        self.assertEqual(m.cells[4], card)
        self.assertTrue(m.undo())
        self.assertIsNone(m.cells[4])
        self.assertEqual(m.tableau[0][-1],card)
        # Empty columns are Kings-only, same-suit stacking required.
        m.tableau[7] = []
        m.tableau[1] = [Card(7,0)]
        m.tableau[2] = [Card(6,1)]
        self.assertFalse(m.move(('t',2,0), ('t',1,0)))
        self.assertFalse(m.move(('t',2,0), ('t',7,0)))
        m.tableau[2] = [Card(6,0)]
        self.assertTrue(m.move(('t',2,0), ('t',1,0)))

    def test_deals_and_undo_for_all_more_games(self):
        for name in MORE_GAMES:
            for seed in range(30):
                with self.subTest(name=name, seed=seed):
                    m = MoreGame(name, seed)
                    self.assertEqual(m.card_count(), 52)
                    self.assertFalse(m.is_won())
                    previous = m._snapshot()
                    self.assertTrue(m.draw())
                    self.assertEqual(m.card_count(),52)
                    self.assertTrue(m.undo())
                    self.assertEqual(m._snapshot(), previous)

    def test_golf_strict_king_and_rank_transition(self):
        m = MoreGame('Golf', 3)
        m.waste = [Card(13,1)]
        m.tableau[0][-1] = Card(12,2)
        self.assertFalse(m.move(('t',0,4), ('w',0,0)))
        m.waste = [Card(11,1)]
        m.tableau[0][-1] = Card(12,2)
        self.assertTrue(m.move(('t',0,4), ('w',0,0)))
        self.assertEqual(m.waste[-1],Card(12,2))
        self.assertEqual(len(m.tableau[0]),4)
        self.assertTrue(m.undo())
        self.assertEqual(len(m.tableau[0]),5)

    def test_tripeaks_cover_graph(self):
        m = MoreGame('TriPeaks',7)
        self.assertEqual(len(m.board),28)
        self.assertEqual(set(i for i in range(28) if m.exposed(i)),set(range(18,28)))
        for i in range(18,28): m.board[i] = None
        self.assertEqual(set(i for i in range(28) if m.exposed(i)),set(range(9,18)))
        for i in range(9,18): m.board[i] = None
        self.assertEqual(set(i for i in range(28) if m.exposed(i)),set(range(3,9)))

    def test_pyramid_pairs_and_exposure(self):
        m = MoreGame('Relaxed Pyramid',1)
        self.assertEqual(len(m.board),28)
        self.assertEqual(set(i for i in range(28) if m.exposed(i)),set(range(21,28)))
        m.board[21] = Card(6,0)
        m.board[22] = Card(7,3)
        self.assertTrue(m.move(('b',21,0), ('b',22,0)))
        self.assertEqual(len(m.removed),2)
        self.assertTrue(m.undo())
        self.assertEqual(len(m.removed),0)
        m.board[21] = Card(13,2)
        self.assertTrue(m.move(('b',21,0), ('discard',0,0)))
        self.assertTrue(m.undo())
        m.board[21] = Card(4,0)
        m.waste = [Card(9,2)]
        self.assertTrue(m.move(('w',0,0), ('b',21,0)))

    def test_pyramid_one_redeal_and_undo(self):
        m = MoreGame('Relaxed Pyramid', 27)
        self.assertEqual(m.redeals_remaining, 1)
        first = []
        for i in range(24):
            first.append(m.stock[-1])
            self.assertTrue(m.draw())
        self.assertTrue(m.draw())
        self.assertEqual(m.redeals_remaining, 0)
        self.assertEqual(m.stock[-1], first[0])
        self.assertTrue(m.undo())
        self.assertEqual(m.redeals_remaining, 1)
        self.assertEqual(m.stock, [])
        self.assertEqual(m.waste, first)
        self.assertEqual(m.card_count(), 52)

    def test_scorpion_packet_stock_and_exposure(self):
        m=MoreGame('Scorpion II', 8)
        self.assertEqual(len(m.stock),3)
        self.assertEqual(m.down,[3,3,3,0,0,0,0])
        self.assertFalse(m.movable(('t',0,0)))
        self.assertTrue(m.movable(('t',0,3)))
        self.assertTrue(m.draw())
        self.assertEqual(len(m.stock),0)
        self.assertEqual(list(map(len,m.tableau)),[8,8,8,7,7,7,7])
        self.assertTrue(m.undo())
        self.assertEqual(list(map(len,m.tableau)),[7]*7)
        # Force a valid same-suit packet transfer from face-up range.
        m.tableau[0] = [Card(11,0),Card(10,0),Card(9,0),Card(5,1),Card(4,2)]
        m.down[0] = 3
        m.tableau[3] = [Card(6,1)]
        self.assertTrue(m.move(('t',0,3), ('t',3,0)))
        self.assertEqual(m.down[0],2)
        self.assertEqual(m.tableau[3][-2:], [Card(5,1),Card(4,2)])
        self.assertTrue(m.undo())
        self.assertEqual(m.down[0],3)

    def test_win_conditions_and_nonwinning_partial_boards(self):
        m=MoreGame('Golf',31)
        m.tableau=[[] for _ in range(7)]
        self.assertTrue(m.is_won())
        m=MoreGame('TriPeaks',31)
        m.board=[None]*28
        self.assertTrue(m.is_won())
        m=MoreGame('Relaxed Pyramid',31)
        m.board=[None]*28
        self.assertTrue(m.is_won())  # remaining stock allowed by RELAXED rule
        m=MoreGame('Scorpion II',31)
        m.stock=[]
        m.down=[0]*7
        m.tableau=[[Card(13-r,suit) for r in range(13)] for suit in range(4)]+[[],[],[]]
        self.assertTrue(m.is_won())
        m.tableau[0][-1]=Card(1,1)
        self.assertFalse(m.is_won())

    def test_random_legal_moves_preserve_cards(self):
        for name in MORE_GAMES:
            for seed in range(45):
                m=MoreGame(name,seed)
                if m.is_golf:
                    refs=[('t',i,len(p)-1) for i,p in enumerate(m.tableau) if p]
                    dest=('w',0,0)
                elif m.is_tripeaks:
                    refs=[('b',i,0) for i in range(28) if m.exposed(i)]
                    dest=('w',0,0)
                elif m.is_pyramid:
                    refs=[('b',i,0) for i in range(28) if m.exposed(i)]
                    refs += [('w',0,0)] if m.waste else []
                    dest=None
                else:
                    refs=[('t',i,j) for i,p in enumerate(m.tableau)
                          for j in range(m.down[i],len(p))]
                    dest=None
                before=m._snapshot()
                moved=False
                for r in refs:
                    ds=([dest] if dest else
                        [('discard',0,0)] + refs if m.is_pyramid else
                        [('t',i,0) for i in range(7)])
                    for d in ds:
                        if m.move(r,d):
                            moved=True
                            self.assertEqual(m.card_count(),52)
                            self.assertTrue(m.undo())
                            self.assertEqual(m._snapshot(),before)
                            break
                    if moved:break

if __name__ == '__main__': unittest.main()
