"""Independent move models for Golf, TriPeaks, Relaxed Pyramid and Scorpion II.

None of these models is used by the original twelve games. The only shared
objects are the immutable card value and the sprite-based UI primitives.
"""
import copy
import random
from .extra_games import Card, standard_deck

MORE_GAMES = ("Golf", "TriPeaks", "Relaxed Pyramid", "Scorpion II")


def _blockers(name):
    """Indexes of the lower cards that must be removed to uncover this card."""
    if name == "Relaxed Pyramid":
        out = []
        for row in range(7):
            for col in range(row + 1):
                base = (row + 1) * (row + 2) // 2
                out.append(()) if row == 6 else out.append((base + col, base + col + 1))
        return tuple(out)
    if name == "TriPeaks":
        out = []
        for i in range(28):
            if i < 3:
                out.append((3 + 2 * i, 4 + 2 * i))
            elif i < 9:
                p, side = divmod(i - 3, 2)
                out.append((9 + 3 * p + side, 10 + 3 * p + side))
            elif i < 18:
                j = i - 9
                out.append((18 + j, 19 + j))
            else:
                out.append(())
        return tuple(out)
    return ()


class MoreGame:
    def __init__(self, name, seed=None):
        if name not in MORE_GAMES:
            raise ValueError('Unknown additional game: ' + name)
        self.name = name
        self.rng = random.Random(seed)
        self.blockers = _blockers(name)
        self.new_game()

    @property
    def is_addiction(self): return False

    @property
    def is_golf(self): return self.name == 'Golf'
    @property
    def is_tripeaks(self): return self.name == 'TriPeaks'
    @property
    def is_pyramid(self): return self.name == 'Relaxed Pyramid'
    @property
    def is_scorpion(self): return self.name == 'Scorpion II'

    def new_game(self):
        deck = standard_deck()
        self.rng.shuffle(deck)
        self.history = []
        self.stock = []
        self.waste = []
        self.tableau = []
        self.board = []
        self.removed = []
        self.down = []
        self.message = ''
        self.redeals_remaining = 1 if self.is_pyramid else 0
        if self.is_golf:
            self.tableau = [[] for _ in range(7)]
            for i, card in enumerate(deck[:35]):
                self.tableau[i % 7].append(card)
            self.waste = [deck[35]]
            self.stock = list(reversed(deck[36:]))
        elif self.is_tripeaks:
            self.board = list(deck[:28])
            self.waste = [deck[28]]
            self.stock = list(reversed(deck[29:]))
        elif self.is_pyramid:
            self.board = list(deck[:28])
            self.stock = list(reversed(deck[28:]))
        elif self.is_scorpion:
            self.tableau = [[] for _ in range(7)]
            for i, card in enumerate(deck[:49]):
                self.tableau[i % 7].append(card)
            self.down = [3, 3, 3, 0, 0, 0, 0]  # Scorpion II's gentler layout
            self.stock = list(reversed(deck[49:]))

    def _snapshot(self):
        return copy.deepcopy((self.tableau, self.board, self.stock, self.waste,
                              self.removed, self.down, self.redeals_remaining,
                              self.message))

    def _commit(self, previous):
        self.history.append(previous)
        self.message = 'Won!' if self.is_won() else ''

    def undo(self):
        if not self.history:
            self.message = 'Nothing to undo'
            return False
        (self.tableau, self.board, self.stock, self.waste,
         self.removed, self.down, self.redeals_remaining,
         self.message) = self.history.pop()
        return True

    def draw(self):
        if not self.stock:
            if self.is_pyramid and self.redeals_remaining and self.waste:
                prior = self._snapshot()
                # Turn the remaining waste stack over without shuffling it.
                # This makes the bottom waste card the next card drawn.
                self.stock = list(reversed(self.waste))
                self.waste.clear()
                self.redeals_remaining -= 1
                self._commit(prior)
                self.message = 'Redeal used (0 left)'
                return True
            self.message = 'Stock empty — no redeal'
            return False
        prior = self._snapshot()
        if self.is_scorpion:
            # The three reserve cards are dealt, left to right, in ONE action.
            for i in range(3):
                self.tableau[i].append(self.stock.pop())
        else:
            self.waste.append(self.stock.pop())
        self._commit(prior)
        return True

    def exposed(self, index):
        return (0 <= index < len(self.board) and self.board[index] is not None
                and all(self.board[j] is None for j in self.blockers[index]))

    def _source(self, ref):
        if ref is None:
            return None
        kind, i, start = ref
        if kind == 'b' and (self.is_pyramid or self.is_tripeaks) and self.exposed(i):
            return [self.board[i]]
        if kind == 't' and 0 <= i < len(self.tableau) and 0 <= start < len(self.tableau[i]):
            if self.is_golf:
                return [self.tableau[i][-1]] if start == len(self.tableau[i]) - 1 else None
            if self.is_scorpion and start >= self.down[i]:
                return self.tableau[i][start:]
        if kind == 'w' and self.is_pyramid and self.waste:
            return [self.waste[-1]]
        return None

    def movable(self, src):
        return self._source(src) is not None

    def _take(self, ref):
        kind, i, start = ref
        if kind == 'b':
            card = self.board[i]
            self.board[i] = None
            return [card]
        if kind == 'w':
            return [self.waste.pop()]
        if kind == 't':
            cards = self.tableau[i][start:]
            del self.tableau[i][start:]
            if self.is_scorpion and self.tableau[i] and len(self.tableau[i]) == self.down[i]:
                self.down[i] -= 1  # expose exactly one previously concealed card
            return cards
        raise ValueError('Unknown source')

    def move(self, src, dst):
        cards = self._source(src)
        if not cards or src == dst:
            return False
        if self.is_golf or self.is_tripeaks:
            if dst[0] != 'w' or not self.waste or len(cards) != 1:
                return False
            rank = self.waste[-1].rank
            # Strict Golf: never place anything ON a King; no A/K wrapping.
            if self.is_golf and rank == 13:
                return False
            if abs(cards[0].rank - rank) != 1:
                return False
            previous = self._snapshot()
            self.waste.extend(self._take(src))
            self._commit(previous)
            return True
        if self.is_pyramid:
            if dst[0] == 'discard':
                if cards[0].rank != 13:
                    return False
                previous = self._snapshot()
                self.removed.extend(self._take(src))
                self._commit(previous)
                return True
            other = self._source(dst)
            if not other or len(other) != 1 or cards[0].rank + other[0].rank != 13:
                return False
            previous = self._snapshot()
            self.removed.extend(self._take(src))
            self.removed.extend(self._take(dst))
            self._commit(previous)
            return True
        if self.is_scorpion:
            if dst[0] != 't' or not 0 <= dst[1] < 7 or src[1] == dst[1]:
                return False
            dst_i = dst[1]
            target = self.tableau[dst_i][-1] if self.tableau[dst_i] else None
            if target is None:
                if cards[0].rank != 13:
                    return False
            elif cards[0].suit != target.suit or cards[0].rank != target.rank - 1:
                return False
            previous = self._snapshot()
            self.tableau[dst_i].extend(self._take(src))
            self._commit(previous)
            return True
        return False

    def is_won(self):
        if self.is_golf:
            return all(not p for p in self.tableau)
        if self.is_tripeaks or self.is_pyramid:
            return not any(self.board)
        if self.is_scorpion:
            if self.stock:
                return False
            occupied = [pile for pile in self.tableau if pile]
            if len(occupied) != 4:
                return False
            return (all(len(pile) == 13 and
                        all(card.suit == pile[0].suit and card.rank == 13 - i
                            for i, card in enumerate(pile)) for pile in occupied)
                    and len({pile[0].suit for pile in occupied}) == 4)
        return False

    def card_count(self):
        return (sum(map(len, self.tableau)) + sum(c is not None for c in self.board)
                + len(self.stock) + len(self.waste) + len(self.removed))
