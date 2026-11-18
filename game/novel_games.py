"""Four rule-isolated patience models: Black Hole, Zodiac, Birthday and Castle.

Each transition is atomic and undoable. No Pygame dependency; the renderer
knows about piles, not rules. Zodiac uses the historical two-phase rules.
"""
from __future__ import annotations

import copy
import random
from .entropy import fresh_seed
from .extra_games import Card, standard_deck, next_rank

NOVEL_GAMES = ("Black Hole", "Zodiac", "Birthday", "Beleaguered Castle")

# German 'Der Geburtstag': a four-digit target WITHOUT zero. The four base
# cards each exceed the corresponding digit by one; suits follow SHDC.
# Change to your own target before starting the program if desired.
BIRTHDAY_TARGET = "1956"


class NovelGame:
    def __init__(self, name, seed=None, birthday_target=BIRTHDAY_TARGET):
        if name not in NOVEL_GAMES:
            raise ValueError(f"Unknown game: {name}")
        if name == 'Birthday' and (len(birthday_target) != 4 or
                any(d not in '123456789' for d in birthday_target)):
            raise ValueError('Birthday target must be four digits, 1–9 (no zeros)')
        self.name = name
        self.birthday_target = birthday_target
        self.rng = random.Random(fresh_seed() if seed is None else seed)
        self.new_game()

    is_grid = False
    is_addiction = False
    is_penguin = False
    is_tommy = False

    @property
    def is_blackhole(self): return self.name == 'Black Hole'
    @property
    def is_zodiac(self): return self.name == 'Zodiac'
    @property
    def is_birthday(self): return self.name == 'Birthday'
    @property
    def is_castle(self): return self.name == 'Beleaguered Castle'
    @property
    def phase_two(self):
        return self.is_zodiac and not self.stock and not self.waste

    def new_game(self):
        deck = standard_deck() * (2 if self.is_zodiac else 1)
        self.rng.shuffle(deck)
        self.history = []
        self.tableau = []
        self.cells = []
        self.foundations = []
        self.stock = []
        self.waste = []
        self.passes = 1
        self.message = ''
        if self.is_blackhole:
            base = Card(1, 0)  # Ace of Spades
            deck.remove(base)
            self.foundations = [[base]]
            self.tableau = [[] for _ in range(17)]
            for i, card in enumerate(deck):
                self.tableau[i % 17].append(card)
        elif self.is_castle:
            self.foundations = [[Card(1, suit)] for suit in range(4)]
            deck = [card for card in deck if card.rank != 1]
            self.tableau = [[] for _ in range(8)]
            for i, card in enumerate(deck):
                self.tableau[i % 8].append(card)
        elif self.is_birthday:
            bases = [Card(int(digit) + 1, suit)
                     for suit, digit in enumerate(self.birthday_target)]
            self.foundations = [[c] for c in bases]
            for card in bases:
                deck.remove(card)
            self.stock = list(reversed(deck))
        elif self.is_zodiac:
            self.cells = deck[:8]
            self.tableau = [[] for _ in range(24)]
            for i, card in enumerate(deck[8:32]):
                self.tableau[i].append(card)
            self.stock = list(reversed(deck[32:]))
            self.foundations = [[] for _ in range(8)]
        assert self.card_count() == (104 if self.is_zodiac else 52)

    def _snapshot(self):
        return copy.deepcopy((self.tableau, self.cells, self.foundations,
                              self.stock, self.waste, self.passes, self.message))

    def undo(self):
        if not self.history:
            self.message = 'Nothing to undo'
            return False
        (self.tableau, self.cells, self.foundations,
         self.stock, self.waste, self.passes, self.message) = self.history.pop()
        return True

    def _commit(self, previous):
        self.history.append(previous)
        self.message = 'Won!' if self.is_won() else ''

    def draw(self):
        if not (self.is_zodiac or self.is_birthday):
            self.message = 'This game has no stock'
            return False
        if self.stock:
            prev = self._snapshot()
            self.waste.append(self.stock.pop())
            self._commit(prev)
            return True
        if not self.waste:
            self.message = 'No cards left in the stock'
            return False
        if self.is_birthday and self.passes >= 4:
            self.message = 'Four passes exhausted'
            return False
        prev = self._snapshot()
        # Preserve order: first card originally drawn becomes next to be drawn.
        self.stock = list(reversed(self.waste))
        self.waste.clear()
        self.passes += 1
        self._commit(prev)
        self.message = 'Pass ' + str(self.passes) + (' of 4' if self.is_birthday else '')
        return True

    def _source(self, src):
        if not src:
            return None
        kind, i, idx = src
        if kind == 't' and 0 <= i < len(self.tableau):
            pile = self.tableau[i]
            return [pile[-1]] if pile and idx == len(pile) - 1 else None
        if kind == 'c' and 0 <= i < len(self.cells):
            return [self.cells[i]] if self.cells[i] is not None else None
        if kind == 'w' and self.waste:
            return [self.waste[-1]]
        return None

    def movable(self, src):
        return bool(self._source(src))

    def _can_move(self, src, dst, card):
        s, si, _ = src
        d, di, _ = dst
        if self.is_blackhole:
            if s != 't' or d != 'f' or di != 0:
                return False
            return (card.rank - self.foundations[0][-1].rank) % 13 in (1, 12)
        if self.is_castle:
            if s != 't': return False
            if d == 't' and di != si and 0 <= di < 8:
                top = self.tableau[di][-1] if self.tableau[di] else None
                return top is None or card.rank == top.rank - 1
            if d == 'f' and 0 <= di < 4:
                top = self.foundations[di][-1]
                return card.suit == di and card.rank == top.rank + 1
            return False
        if self.is_birthday:
            if s != 'w' or d != 'f' or not 0 <= di < 4:
                return False
            top = self.foundations[di][-1]
            return (card.suit == di and len(self.foundations[di]) < 13
                    and card.rank == next_rank(top.rank))
        if self.is_zodiac:
            if not self.phase_two:
                if s not in ('w', 'c'):
                    return False
                if d == 'c' and s == 'w' and 0 <= di < 8:
                    return self.cells[di] is None
                if d == 't' and 0 <= di < 24:
                    top = self.tableau[di][-1] if self.tableau[di] else None
                    return (top is not None and card.suit == top.suit
                            and abs(card.rank - top.rank) == 1)
                return False
            if s not in ('t', 'c') or d != 'f' or not 0 <= di < 8:
                return False
            if card.suit != di % 4:
                return False
            pile = self.foundations[di]
            if not pile:
                return card.rank == (1 if di < 4 else 13)
            return card.rank == pile[-1].rank + (1 if di < 4 else -1)
        return False

    def move(self, src, dst):
        if src == dst:
            return False
        cards = self._source(src)
        if not cards:
            self.message = 'Only exposed cards can move'
            return False
        if not self._can_move(src, dst, cards[0]):
            if self.is_zodiac and not self.phase_two and dst[0] == 'f':
                self.message = 'Foundations unlock when stock and waste are cleared'
            elif self.is_birthday:
                self.message = 'Build up one rank in the same suit (wrap K to A)'
            else:
                self.message = 'Illegal destination for this game'
            return False
        prev = self._snapshot()
        sk, si, _ = src
        dk, di, _ = dst
        if sk == 't':
            card = self.tableau[si].pop()
        elif sk == 'c':
            card = self.cells[si]
            self.cells[si] = None
        else:
            card = self.waste.pop()
        if dk == 't':
            self.tableau[di].append(card)
        elif dk == 'c':
            self.cells[di] = card
        else:
            self.foundations[di].append(card)
        self._commit(prev)
        assert self.card_count() == (104 if self.is_zodiac else 52)
        return True

    def move_home(self, src):
        cards = self._source(src)
        if not cards:
            return False
        card = cards[0]
        if self.is_zodiac:
            targets = (card.suit, card.suit + 4)
        elif self.is_birthday or self.is_castle:
            targets = (card.suit,)
        else:
            targets = (0,)
        for i in targets:
            if self._can_move(src, ('f', i, 0), card):
                return self.move(src, ('f', i, 0))
        self.message = 'No eligible foundation for this card'
        return False

    def is_won(self):
        if self.is_blackhole:
            return len(self.foundations[0]) == 52
        if self.is_zodiac:
            return all(len(pile) == 13 for pile in self.foundations)
        return all(len(pile) == 13 for pile in self.foundations)

    def card_count(self):
        return (sum(map(len, self.tableau)) +
                sum(c is not None for c in self.cells) +
                sum(map(len, self.foundations)) + len(self.stock) + len(self.waste))
