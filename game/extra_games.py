"""Move rules for the original six extensions and two related variants. UI uses the original card sheet and painter.
The six original Variant and Table rules remain untouched.
"""
from dataclasses import dataclass
import copy
import random

from .entropy import fresh_seed

from .rules import EXTRA_FAMILY_GAMES

SUIT_MARKS = ("♠", "♥", "♦", "♣")
SUIT_NAMES = ("Spades", "Hearts", "Diamonds", "Clubs")
RANK_TEXT = ("", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")


@dataclass(frozen=True)
class Card:
    rank: int
    suit: int

    @property
    def red(self):
        return self.suit in (1, 2)

    @property
    def face_up(self):
        """All extended-game tableau cards are face up."""
        return True

    def __str__(self):
        return RANK_TEXT[self.rank] + SUIT_MARKS[self.suit]


def standard_deck():
    return [Card(rank, suit) for suit in range(4) for rank in range(1, 14)]


def next_rank(rank):
    return 1 if rank == 13 else rank + 1


def previous_rank(rank):
    return 13 if rank == 1 else rank - 1


class ExtraGame:
    """Reversible state transitions with no dependency on the existing game."""

    def __init__(self, name, seed=None):
        if name not in EXTRA_FAMILY_GAMES:
            raise ValueError("Unknown game: %r" % name)
        self.name = name
        self.rng = random.Random(fresh_seed() if seed is None else seed)
        self.history = []
        self.new_game()

    @property
    def is_freecell(self):
        return self.name in ("FreeCell", "Eight Off")

    @property
    def is_eightoff(self):
        return self.name == "Eight Off"

    @property
    def is_australian_redeal(self):
        return self.name == "Australian Patience (One Redeal)"

    @property
    def is_penguin(self):
        return self.name == "Penguin"

    @property
    def is_australian(self):
        return self.name in ("Australian Patience", "Australian Patience (One Redeal)")

    @property
    def is_tommy(self):
        return self.name == "Old Patience / Sir Tommy"

    @property
    def is_addiction(self):
        return self.name == "Addiction Solitaire"

    @property
    def is_maze(self):
        return self.name == "Maze Solitaire"

    @property
    def is_grid(self):
        return self.is_addiction or self.is_maze

    def new_game(self):
        deck = standard_deck()
        self.rng.shuffle(deck)
        self.history = []
        self.tableau = []
        self.cells = []
        self.foundations = [[] for _ in range(4)]
        self.stock = []
        self.waste = []
        self.pending = None
        self.grid = []
        self.beak_rank = None
        self.reshuffles = 0
        self.redeals_remaining = 1 if self.is_australian_redeal else 0
        self.message = ""
        if self.is_freecell:
            self.tableau = [[] for _ in range(8)]
            if self.is_eightoff:
                for i, card in enumerate(deck[:48]):
                    self.tableau[i % 8].append(card)
                self.cells = list(deck[48:]) + [None] * 4
            else:
                for i, card in enumerate(deck):
                    self.tableau[i % 8].append(card)
                self.cells = [None] * 4
        elif self.is_penguin:
            self.tableau = [[] for _ in range(7)]
            self.cells = [None] * 7
            self.beak_rank = deck[0].rank
            played = 0
            for card in deck:
                if card.rank == self.beak_rank and card != deck[0]:
                    self.foundations[card.suit].append(card)
                else:
                    self.tableau[played % 7].append(card)
                    played += 1
        elif self.is_australian:
            self.tableau = [[] for _ in range(7)]
            for i, card in enumerate(deck[:28]):
                self.tableau[i % 7].append(card)
            self.stock = list(reversed(deck[28:]))  # .pop() follows the shuffled deal
        elif self.is_tommy:
            self.tableau = [[] for _ in range(8)]  # Wikipedia Sir Tommy: eight waste piles
            self.stock = list(reversed(deck))
        elif self.is_addiction:
            self.grid = [None if c.rank == 1 else c for c in deck]
            self.reshuffles = 3
        elif self.is_maze:
            # 54 ring positions: 8 cards + gap, 8 cards + gap, 4 x 9 cards.
            self.grid = deck[:8] + [None] + deck[8:16] + [None] + deck[16:]
            self.grid = [None if c is not None and c.rank == 13 else c
                         for c in self.grid]

    def _snapshot(self):
        return copy.deepcopy((self.tableau, self.cells, self.foundations,
                              self.stock, self.waste, self.pending,
                              self.grid, self.reshuffles, self.redeals_remaining, self.message))

    def _restore(self, snapshot):
        (self.tableau, self.cells, self.foundations,
         self.stock, self.waste, self.pending,
         self.grid, self.reshuffles, self.redeals_remaining, self.message) = copy.deepcopy(snapshot)

    def _commit(self, snapshot):
        self.history.append(snapshot)
        self.message = "Won!" if self.is_won() else ""

    def undo(self):
        if not self.history:
            self.message = "Nothing to undo"
            return False
        self._restore(self.history.pop())
        return True

    def draw(self):
        if not (self.is_australian or self.is_tommy):
            return False
        if self.is_tommy and self.pending is not None:
            self.message = "Place the revealed card first"
            return False
        if not self.stock:
            if self.is_australian_redeal and self.redeals_remaining and self.waste:
                before = self._snapshot()
                self.stock = list(reversed(self.waste))
                self.waste.clear()
                self.redeals_remaining -= 1
                self._commit(before)
                self.message = "One redeal used"
                return True
            self.message = "Stock empty — no redeals"
            return False
        before = self._snapshot()
        card = self.stock.pop()
        if self.is_tommy:
            self.pending = card
        else:
            self.waste.append(card)
        self._commit(before)
        return True

    def reshuffle(self):
        if not self.is_addiction or not self.reshuffles or self.is_won():
            self.message = "No reshuffles left" if self.is_addiction else ""
            return False
        # In the Gaps/Addiction rules, a round ends only after no more
        # placements are possible; reshuffling early is not a legal move.
        if self.has_grid_move():
            self.message = "Moves remain — play those before reshuffling"
            return False
        before = self._snapshot()
        # Keep in-suit runs beginning with a deuce in the leftmost slot.
        keep = [0] * 4
        for row in range(4):
            first = self.grid[row * 13]
            if first is None or first.rank != 2:
                continue
            suit = first.suit
            for col in range(12):
                card = self.grid[row * 13 + col]
                if card is not None and card.suit == suit and card.rank == col + 2:
                    keep[row] += 1
                else:
                    break
        retained = {row * 13 + col for row in range(4) for col in range(keep[row])}
        cards = [c for i, c in enumerate(self.grid) if i not in retained and c is not None]
        self.rng.shuffle(cards)
        # Four mandatory gaps, immediately after the retained sequences.
        gaps = {row * 13 + keep[row] for row in range(4)}
        positions = [i for i in range(52) if i not in retained and i not in gaps]
        assert len(positions) == len(cards)
        for i in range(52):
            if i not in retained:
                self.grid[i] = None
        for pos, card in zip(positions, cards):
            self.grid[pos] = card
        self.reshuffles -= 1
        self._commit(before)
        return True

    def _source(self, src):
        kind, pile, index = src
        if kind == "t":
            if pile >= len(self.tableau) or not 0 <= index < len(self.tableau[pile]):
                return None
            cards = self.tableau[pile][index:]
            if self.is_tommy and len(cards) != 1:
                return None
            if self.is_australian:
                return cards  # Yukon lift, unordered packet
            if self.is_freecell:
                valid = all((upper.suit == lower.suit if self.is_eightoff else upper.red != lower.red) and
                            upper.rank == lower.rank + 1
                            for upper, lower in zip(cards, cards[1:]))
                return cards if valid else None
            if self.is_penguin:
                valid = all(upper.suit == lower.suit and
                            previous_rank(upper.rank) == lower.rank
                            for upper, lower in zip(cards, cards[1:]))
                return cards if valid else None
            return cards if len(cards) == 1 else None
        if kind == "c" and 0 <= pile < len(self.cells) and self.cells[pile]:
            return [self.cells[pile]]
        if kind == "w" and self.is_australian and self.waste:
            return [self.waste[-1]]
        if kind == "p" and self.is_tommy and self.pending:
            return [self.pending]
        if kind == "g" and self.is_grid and 0 <= pile < len(self.grid):
            return [self.grid[pile]] if self.grid[pile] is not None else None
        return None

    def movable(self, src):
        return self._source(src) is not None

    def grid_legal_moves(self):
        """All valid (card position, gap position) pairs for the gap games.

        Used for hints and touch affordances; same predicate as actual moves.
        """
        if not self.is_grid:
            return []
        gaps = [i for i, c in enumerate(self.grid) if c is None]
        return [(i, j) for i, card in enumerate(self.grid) if card is not None
                for j in gaps if self._can_fill_gap(card, j)]

    def has_grid_move(self):
        return bool(self.grid_legal_moves())

    def _can_fill_gap(self, card, position):
        if self.grid[position] is not None:
            return False
        if self.is_addiction:
            col = position % 13
            if col == 0:
                return card.rank == 2
            left = self.grid[position - 1]
            return (left is not None and left.rank != 13 and
                    card.suit == left.suit and card.rank == left.rank + 1)
        if self.is_maze:
            n = len(self.grid)
            left = self.grid[(position - 1) % n]
            right = self.grid[(position + 1) % n]
            left_ok = left is not None and (
                (left.rank == 12 and card.rank == 1) or
                (left.rank < 12 and card.suit == left.suit and card.rank == left.rank + 1))
            right_ok = (right is not None and right.rank > 1 and
                        card.suit == right.suit and card.rank == right.rank - 1)
            return left_ok or right_ok
        return False

    def move(self, src, dst):
        """Move by source/destination addresses: ('t', column, start), etc.

        t=tableau, c=cell, w=Australian waste, p=Sir Tommy pending card,
        f=foundation, g=fixed grid slot. No mutation on an illegal move.
        """
        if src == dst:
            return False
        cards = self._source(src)
        if not cards:
            self.message = "That card cannot move"
            return False
        source_kind, source_i, start_i = src
        target_kind, target_i, _ = dst
        if self.is_grid:
            if (source_kind != "g" or target_kind != "g" or
                    not 0 <= target_i < len(self.grid) or
                    not self._can_fill_gap(cards[0], target_i)):
                self.message = "Select a legal gap"
                return False
        elif target_kind == "f":
            if len(cards) != 1 or not 0 <= target_i < 4:
                return False
            top = self.foundations[target_i][-1] if self.foundations[target_i] else None
            if self.is_tommy:
                if not (top is None and cards[0].rank == 1 or
                        top is not None and cards[0].rank == top.rank + 1):
                    return False
            else:
                card = cards[0]
                if card.suit != target_i:
                    return False
                base = self.beak_rank if self.is_penguin else 1
                if top is None:
                    if card.rank != base:
                        return False
                elif self.is_penguin:
                    if card.rank != next_rank(top.rank):
                        return False
                elif card.rank != top.rank + 1:
                    return False
        elif target_kind == "c":
            if self.is_tommy or self.is_australian or not 0 <= target_i < len(self.cells):
                return False
            if self.cells[target_i] is not None or len(cards) != 1:
                return False
            if source_kind not in ("t", "c"):
                return False
        elif target_kind == "t":
            if not 0 <= target_i < len(self.tableau):
                return False
            if source_kind == "t" and target_i == source_i:
                return False
            if self.is_tommy:
                if source_kind != "p" or len(cards) != 1:
                    return False  # placed waste cards may ONLY go to foundations
            elif source_kind not in ("t", "c", "w"):
                return False
            top = self.tableau[target_i][-1] if self.tableau[target_i] else None
            if self.is_tommy:
                pass  # pending card may be buried on ANY wastepile
            elif top is None:
                if self.is_eightoff and cards[0].rank != 13:
                    return False
                if self.is_australian and cards[0].rank != 13:
                    return False
                if self.is_penguin and cards[0].rank != previous_rank(self.beak_rank):
                    return False
            elif self.is_penguin:
                if cards[0].suit != top.suit or previous_rank(top.rank) != cards[0].rank:
                    return False
            elif self.is_australian:
                if cards[0].suit != top.suit or cards[0].rank != top.rank - 1:
                    return False
            else:
                if ((cards[0].suit != top.suit if self.is_eightoff else cards[0].red == top.red)
                        or cards[0].rank != top.rank - 1):
                    return False
            if self.is_freecell and len(cards) > 1:
                other_empty = sum(not pile for i, pile in enumerate(self.tableau)
                                  if i != target_i and i != source_i)
                # An empty destination is consumed, so may not act as workspace.
                if target_i != source_i and self.tableau[target_i]:
                    # All other empty piles may act as workspace.
                    other_empty = sum(not pile for i, pile in enumerate(self.tableau)
                                      if i != source_i)
                capacity = (sum(c is None for c in self.cells) + 1) * (2 ** other_empty)
                if len(cards) > capacity:
                    self.message = "Not enough free cells / empty columns"
                    return False
        else:
            return False

        before = self._snapshot()
        if source_kind == "t":
            del self.tableau[source_i][start_i:]
        elif source_kind == "c":
            self.cells[source_i] = None
        elif source_kind == "w":
            self.waste.pop()
        elif source_kind == "p":
            self.pending = None
        elif source_kind == "g":
            self.grid[source_i] = None
        if target_kind == "f":
            self.foundations[target_i].extend(cards)
        elif target_kind == "c":
            self.cells[target_i] = cards[0]
        elif target_kind == "t":
            self.tableau[target_i].extend(cards)
        elif target_kind == "g":
            self.grid[target_i] = cards[0]
        self._commit(before)
        return True

    def move_home(self, src):
        cards = self._source(src)
        if not cards or len(cards) != 1 or self.is_grid:
            return False
        targets = range(4) if self.is_tommy else (cards[0].suit,)
        for target in targets:
            if self.move(src, ("f", target, 0)):
                return True
        self.message = "Cannot move that card home"
        return False

    def is_won(self):
        if self.is_addiction:
            if len(self.grid) != 52:
                return False
            suits = set()
            for row in range(4):
                chunk = self.grid[row * 13:(row + 1) * 13]
                if chunk[0] is None:
                    return False
                suit = chunk[0].suit
                if suit in suits:
                    return False
                suits.add(suit)
                if any(c != Card(col + 2, suit) for col, c in enumerate(chunk[:12])):
                    return False
                if chunk[12] is not None:
                    return False
            return True
        if self.is_maze:
            if self.grid[0] is None or self.grid[0].rank != 1:
                return False
            if self.grid[-1] is None or self.grid[-1].rank != 12:
                return False
            cards = [c for c in self.grid if c is not None]
            if len(cards) != 48:
                return False
            suits = set()
            for start in (0, 12, 24, 36):
                chunk = cards[start:start + 12]
                suit = chunk[0].suit
                if suit in suits or any(c != Card(i + 1, suit) for i, c in enumerate(chunk)):
                    return False
                suits.add(suit)
            return True
        return sum(map(len, self.foundations)) == 52

    def card_count(self):
        return (sum(map(len, self.tableau)) + sum(c is not None for c in self.cells) +
                sum(map(len, self.foundations)) + len(self.stock) + len(self.waste) +
                (self.pending is not None) + sum(c is not None for c in self.grid))
