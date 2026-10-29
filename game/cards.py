"""The cards. The suit constants are the sheet's own row order, which puts the two red suits next to each other — so `red` is a single comparison."""
import random

SPADES = 0
HEARTS = 1
DIAMONDS = 2
CLUBS = 3
SUITS = (SPADES, HEARTS, DIAMONDS, CLUBS)

ACE = 1
KING = 13
RANKS = tuple(range(ACE, KING + 1))

RANK_MARKS = {ACE: "A", 11: "J", 12: "Q", 13: "K"}
SUIT_MARKS = ("♠", "♥", "♦", "♣")


class Card:
    """`face_up` is the only thing about a card that ever changes."""

    __slots__ = ("suit", "rank", "face_up")

    def __init__(self, suit, rank, face_up=False):
        self.suit = suit
        self.rank = rank
        self.face_up = face_up

    @property
    def red(self):
        return HEARTS <= self.suit <= DIAMONDS

    def __repr__(self):
        return "%s%s" % (RANK_MARKS.get(self.rank, self.rank), SUIT_MARKS[self.suit])


def new_deck(rng=None, suits=SUITS, copies=1):
    """Pass a seeded `random.Random` as `rng` to deal the same hand again."""
    deck = [Card(suit, rank)
            for _ in range(copies) for suit in suits for rank in RANKS]
    (rng or random).shuffle(deck)
    return deck
