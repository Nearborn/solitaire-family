"""The rules — legality, and nothing else, for all six games on this table. Nothing here touches the table or moves anything; each thing the six disagree about is a small named rule below."""
from .cards import ACE, HEARTS, KING, RANKS, SPADES, SUITS


# -- how a column is built --


def alternating_colours(card, top):
    return card.red != top.red and card.rank == top.rank - 1


def any_suit(card, top):
    return card.rank == top.rank - 1


# -- what may start an empty column --


def only_a_king(card):
    return card.rank == KING


def any_card(_card):
    return True


# -- what may be lifted off a column --


def all_face_up(cards):
    return bool(cards) and all(card.face_up for card in cards)


def a_built_run(cards, builds_on):
    if not all_face_up(cards):
        return False
    return all(builds_on(lower, upper) for upper, lower in zip(cards, cards[1:]))


def any_face_up_card(cards, _builds_on):
    """Yukon: whatever sits on the card, in any order at all."""
    return all_face_up(cards)


def a_same_suit_run(cards, _builds_on):
    """Spider builds loosely and lifts strictly, so this cannot use `builds_on`."""
    if not all_face_up(cards):
        return False
    return all(lower.suit == upper.suit and lower.rank == upper.rank - 1
               for upper, lower in zip(cards, cards[1:]))


# -- going home --


def one_card_home(cards, top):
    """An empty foundation arrives as `top` of None."""
    if len(cards) != 1:
        return False
    card = cards[0]
    if top is None:
        return card.rank == ACE
    return card.suit == top.suit and card.rank == top.rank + 1


def a_finished_run(cards, top):
    """A King-to-Ace run of one suit, onto an empty foundation."""
    if top is not None or len(cards) != len(RANKS):
        return False
    return (cards[0].rank == KING
            and all(card.suit == cards[0].suit for card in cards)
            and all(lower.rank == upper.rank - 1
                    for upper, lower in zip(cards, cards[1:])))


# -- what the face-down pile does --


class Stock:
    """A tap does nothing, turns `to_waste` cards onto the waste, or deals one face up to every column."""

    __slots__ = ("to_waste", "across_the_columns")

    def __init__(self, to_waste=0, across_the_columns=False):
        self.to_waste = to_waste
        self.across_the_columns = across_the_columns

    @property
    def deals_anything(self):
        return self.to_waste > 0 or self.across_the_columns

    @property
    def keeps_a_waste(self):
        return self.to_waste > 0


NO_STOCK = Stock()
TURN_ONE_OVER = Stock(to_waste=1)
TURN_THREE_OVER = Stock(to_waste=3)
DEAL_ACROSS_THE_COLUMNS = Stock(across_the_columns=True)


# -- how the cards start out --


class Deal:
    """Two numbers per column; the column count, what is left for the stock and the dealing order all follow."""

    __slots__ = ("face_down", "face_up", "counts", "order")

    def __init__(self, face_down, face_up):
        self.face_down = tuple(face_down)
        self.face_up = tuple(face_up)
        self.counts = tuple(down + up for down, up in zip(self.face_down, self.face_up))
        # `play.py` deals the opening animation from this same order.
        self.order = tuple(index
                           for round_number in range(max(self.counts, default=0))
                           for index, count in enumerate(self.counts)
                           if count > round_number)

    @property
    def columns(self):
        return len(self.counts)

    @property
    def dealt(self):
        """The rest of the deck starts in the stock."""
        return sum(self.counts)


#: Klondike's, which Draw Three shares; twenty-four undealt.
KLONDIKE_DEAL = Deal(face_down=(0, 1, 2, 3, 4, 5, 6),
                     face_up=(1, 1, 1, 1, 1, 1, 1))

#: Yukon's: all fifty-two, so no stock.
OPEN_DEAL = Deal(face_down=(0, 1, 2, 3, 4, 5, 6),
                 face_up=(1, 5, 5, 5, 5, 5, 5))

#: Spider's: fifty-four of a hundred and four; the fifty left are five rows off the stock.
SPIDER_DEAL = Deal(face_down=(5, 5, 5, 5, 4, 4, 4, 4, 4, 4),
                   face_up=(1, 1, 1, 1, 1, 1, 1, 1, 1, 1))


# -- the six rule sets --


class Variant:
    """Everything with a default is something most of these games agree about, so a `Variant` only states what it changes."""

    __slots__ = ("name", "short_name", "shows_suits", "builds_on", "lift", "deal", "stock",
                 "suits", "copies", "empty_column", "foundation_takes", "home_lift",
                 "runs_leave_on_their_own")

    def __init__(self, name, short_name, builds_on, lift, deal, stock,
                 suits=SUITS, copies=1, empty_column=only_a_king,
                 foundation_takes=one_card_home, home_lift=1,
                 runs_leave_on_their_own=False, shows_suits=False):
        self.name = name
        self.short_name = short_name
        #: The three Spiders share a name, so their plate draws a dot per suit after it.
        self.shows_suits = shows_suits
        self.builds_on = builds_on
        self.lift = lift
        self.deal = deal
        self.stock = stock
        self.suits = tuple(suits)
        self.copies = copies
        self.empty_column = empty_column
        self.foundation_takes = foundation_takes
        #: Cards to a foundation in one lift: one, or Spider's whole run.
        self.home_lift = home_lift
        #: Only Spider, where a run goes the instant its last card lands.
        self.runs_leave_on_their_own = runs_leave_on_their_own

    # -- the deck, and how many piles it needs --

    @property
    def deck_size(self):
        return len(self.suits) * len(RANKS) * self.copies

    @property
    def column_count(self):
        return self.deal.columns

    @property
    def foundation_count(self):
        return self.deck_size // len(RANKS)

    # -- what may sit where --

    def sits_on_tableau(self, card, top):
        """An empty column arrives as `top` of None."""
        if top is None:
            return self.empty_column(card)
        return self.builds_on(card, top)

    def is_liftable(self, cards):
        return self.lift(cards, self.builds_on)

    def goes_home(self, cards, top):
        """A stack, because Spider's foundations take a whole run."""
        return self.foundation_takes(cards, top)

    def is_won(self, foundations):
        return (len(foundations) == self.foundation_count
                and all(len(pile) == len(RANKS) for pile in foundations))

    # -- the face-down pile --

    @property
    def has_stock(self):
        return self.stock.deals_anything

    @property
    def has_waste(self):
        return self.stock.keeps_a_waste

    def __repr__(self):
        return "<%s>" % self.name


KLONDIKE = Variant(
    name="Klondike", short_name="Klondike",
    builds_on=alternating_colours, lift=a_built_run,
    deal=KLONDIKE_DEAL, stock=TURN_ONE_OVER)

DRAW_THREE = Variant(
    name="Klondike Draw Three", short_name="Draw Three",
    builds_on=alternating_colours, lift=a_built_run,
    deal=KLONDIKE_DEAL, stock=TURN_THREE_OVER)

YUKON = Variant(
    name="Yukon", short_name="Yukon",
    builds_on=alternating_colours, lift=any_face_up_card,
    deal=OPEN_DEAL, stock=NO_STOCK)

SPIDER_ONE_SUIT = Variant(
    name="Spider (One Suit)", short_name="Spider", shows_suits=True,
    builds_on=any_suit, lift=a_same_suit_run,
    deal=SPIDER_DEAL, stock=DEAL_ACROSS_THE_COLUMNS,
    suits=(SPADES,), copies=8,
    empty_column=any_card, foundation_takes=a_finished_run, home_lift=len(RANKS),
    runs_leave_on_their_own=True)

SPIDER_TWO_SUITS = Variant(
    name="Spider (Two Suits)", short_name="Spider", shows_suits=True,
    builds_on=any_suit, lift=a_same_suit_run,
    deal=SPIDER_DEAL, stock=DEAL_ACROSS_THE_COLUMNS,
    suits=(SPADES, HEARTS), copies=4,
    empty_column=any_card, foundation_takes=a_finished_run, home_lift=len(RANKS),
    runs_leave_on_their_own=True)

SPIDER_FOUR_SUITS = Variant(
    name="Spider (Four Suits)", short_name="Spider", shows_suits=True,
    builds_on=any_suit, lift=a_same_suit_run,
    deal=SPIDER_DEAL, stock=DEAL_ACROSS_THE_COLUMNS,
    suits=SUITS, copies=2,
    empty_column=any_card, foundation_takes=a_finished_run, home_lift=len(RANKS),
    runs_leave_on_their_own=True)

#: gentlest first
VARIANTS = (KLONDIKE, DRAW_THREE, YUKON,
            SPIDER_ONE_SUIT, SPIDER_TWO_SUITS, SPIDER_FOUR_SUITS)


# -- six additional tables (the original six Variant instances above are unchanged) --
# These require free cells, a pending stock card, or a fixed gap grid. Their
# specialized move logic lives in extra_games.py, never in classic Table.
ADDITIONAL_GAMES = (
    "FreeCell", "Penguin", "Australian Patience",
    "Old Patience / Sir Tommy", "Addiction Solitaire", "Maze Solitaire",
)


EXTRA_FAMILY_GAMES = ADDITIONAL_GAMES + ("Australian Patience (One Redeal)", "Eight Off")


class SpecialVariant:
    """Menu/layout metadata; not a replacement for the classic Variant rules."""

    def __init__(self, name, short_name, columns, foundations, stock=False, waste=False):
        self.name = name
        self.short_name = short_name
        self.column_count = columns
        self.foundation_count = foundations
        self.has_stock = stock
        self.has_waste = waste
        self.shows_suits = False
        self.suits = ()


SPECIAL_VARIANTS = (
    SpecialVariant("FreeCell", "FreeCell", 8, 4),
    SpecialVariant("Penguin", "Penguin", 7, 4),
    SpecialVariant("Australian Patience", "Australian", 7, 4, True, True),
    SpecialVariant("Old Patience / Sir Tommy", "Sir Tommy", 8, 4, True, True),
    SpecialVariant("Addiction Solitaire", "Addiction", 13, 0),
    SpecialVariant("Maze Solitaire", "Maze", 9, 0),
    SpecialVariant("Australian Patience (One Redeal)", "Australian +1", 7, 4, True, True),
    SpecialVariant("Eight Off", "Eight Off", 8, 4),
    SpecialVariant("Golf", "Golf", 7, 0, True, True),
    SpecialVariant("TriPeaks", "TriPeaks", 10, 0, True, True),
    SpecialVariant("Relaxed Pyramid", "Pyramid", 7, 0, True, True),
    SpecialVariant("Scorpion II", "Scorpion II", 7, 0, True, False),
)
