"""The piles, the deal, and the move log that undo runs backwards.

Nothing here changes except through a `Transfer` or a `Flip`, and each can say what its own opposite is. An action is a LIST of moves, which lets a rule set do something big in one undoable step.
"""
from .cards import new_deck
from .entropy import fresh_rng
from .rules import KLONDIKE

# A pile is named by a (kind, number) pair, so it can be passed about without knowing where it is drawn.
STOCK = ("stock", 0)
WASTE = ("waste", 0)


def foundation(index):
    return ("foundation", index)


def column(index):
    return ("tableau", index)


# Every rule set states its own order in `rules.py`.
DEAL_ORDER = KLONDIKE.deal.order


# -- the two kinds of move --


class Transfer:
    """`face_up_before` is what the inverse needs; `turned_over` reverses the block on the way, the way a hand turns three cards over."""

    __slots__ = ("source", "destination", "count", "face_up", "face_up_before", "turned_over")

    def __init__(self, source, destination, count, face_up, face_up_before, turned_over=False):
        self.source = source
        self.destination = destination
        self.count = count
        self.face_up = face_up
        self.face_up_before = face_up_before
        self.turned_over = turned_over

    def inverse(self):
        """`turned_over` is carried across unchanged: turning the block again restores the order."""
        return Transfer(self.destination, self.source, self.count,
                        self.face_up_before, self.face_up, self.turned_over)

    def apply(self, table):
        cards = table.pile(self.source)
        cut = len(cards) - self.count
        moved = cards[cut:]
        del cards[cut:]
        if self.turned_over:
            moved.reverse()
        for card in moved:
            card.face_up = self.face_up
        table.pile(self.destination).extend(moved)


class Flip:
    __slots__ = ("pile", "face_up")

    def __init__(self, pile, face_up):
        self.pile = pile
        self.face_up = face_up

    def inverse(self):
        return Flip(self.pile, not self.face_up)

    def apply(self, table):
        table.pile(self.pile)[-1].face_up = self.face_up


def undo_of(moves):
    return [move.inverse() for move in reversed(moves)]


# -- the table --


class Table:
    def __init__(self, variant=None, rng=None):
        self.variant = variant or KLONDIKE
        self.new_deal(rng)

    def new_deal(self, rng=None, variant=None):
        """The one change no undo reaches — the log starts here — and the only way a rule set changes."""
        if variant is not None:
            self.variant = variant
        variant = self.variant
        deal = variant.deal
        deck = new_deck(rng if rng is not None else fresh_rng(),
                        suits=variant.suits, copies=variant.copies)
        self.foundations = [[] for _ in range(variant.foundation_count)]
        self.columns = [[] for _ in range(variant.column_count)]
        self.waste = []
        self.history = []
        for index in deal.order:
            self.columns[index].append(deck.pop())
        for index, pile in enumerate(self.columns):
            for card in pile[len(pile) - deal.face_up[index]:]:
                card.face_up = True
        self.stock = deck  # nothing at all in Yukon

    def pile(self, identifier):
        kind, index = identifier
        if kind == "tableau":
            return self.columns[index]
        if kind == "foundation":
            return self.foundations[index]
        return self.waste if kind == "waste" else self.stock

    def top(self, identifier):
        cards = self.pile(identifier)
        return cards[-1] if cards else None

    def do(self, moves, before_tidying=None):
        """Carry one action out, and remember how to take it back.

        Whatever the table then does by itself rides in the same action, so one undo puts both back. `before_tidying` runs between the two — moves made, table not yet tidied — the only moment a finished run is still lying in its column.
        """
        moves = list(moves)
        for move in moves:
            move.apply(self)
        if before_tidying is not None:
            before_tidying()
        moves.extend(lift_finished_runs(self))
        self.history.append(moves)
        return moves

    def can_undo(self):
        return bool(self.history)

    def undo(self):
        if not self.history:
            return False
        for move in undo_of(self.history.pop()):
            move.apply(self)
        return True

    def is_won(self):
        return self.variant.is_won(self.foundations)


# -- the move builders --


def deal_from_stock(table):
    stock = table.variant.stock
    if stock.across_the_columns:
        return _deal_across_the_columns(table)
    count = min(stock.to_waste, len(table.stock))
    if not count:
        return None
    return [Transfer(STOCK, WASTE, count,
                     face_up=True, face_up_before=False, turned_over=True)]


def _deal_across_the_columns(table):
    """A card to every column as ONE action, so the row lands together and one undo takes it all back. Refused while a column is empty: a card dealt into a gap fills the one place a stuck run could have gone."""
    if len(table.stock) < len(table.columns) or _any_column_is_empty(table):
        return None
    return [Transfer(STOCK, column(index), 1, face_up=True, face_up_before=False)
            for index in range(len(table.columns))]


def _any_column_is_empty(table):
    return any(not cards for cards in table.columns)


def stock_refused_by_an_empty_column(table):
    """A refusal the player can do something about, unlike a spent stock."""
    return (table.variant.stock.across_the_columns
            and len(table.stock) >= len(table.columns)
            and _any_column_is_empty(table))


def recycle_waste(table):
    """Only offered once the stock is empty, which makes going round again deliberate."""
    if not table.variant.has_waste or table.stock or not table.waste:
        return None
    return [Transfer(WASTE, STOCK, len(table.waste),
                     face_up=False, face_up_before=True, turned_over=True)]


def liftable(table, source, index):
    cards = table.pile(source)
    if index < 0 or index >= len(cards):
        return 0
    kind = source[0]
    if kind in ("waste", "foundation"):
        return 1 if index == len(cards) - 1 else 0
    if kind == "tableau" and table.variant.is_liftable(cards[index:]):
        return len(cards) - index
    return 0


def exposing_flip(table, source, count):
    if source[0] != "tableau":
        return None
    cards = table.pile(source)
    uncovered = len(cards) - count - 1
    if uncovered < 0 or cards[uncovered].face_up:
        return None
    return Flip(source, True)


def move_to(table, source, count, destination):
    """The single door every placement goes through. A move that uncovers a face-down card carries the flip in the same list, so it is one undo."""
    if destination == source:
        return None
    cards = table.pile(source)
    if count < 1 or count > len(cards):
        return None
    moving = cards[len(cards) - count:]
    # A stack the rule set lets travel, or the top card only off the waste or a foundation.
    if source[0] == "tableau":
        if not table.variant.is_liftable(moving):
            return None
    elif count != 1 or not moving[0].face_up:
        return None
    kind = destination[0]
    if kind == "foundation":
        if not table.variant.goes_home(moving, table.top(destination)):
            return None
    elif kind == "tableau":
        if not table.variant.sits_on_tableau(moving[0], table.top(destination)):
            return None
    else:
        return None  # nothing is ever put back onto the stock or the waste
    moves = [Transfer(source, destination, count, face_up=True, face_up_before=True)]
    flip = exposing_flip(table, source, count)
    if flip is not None:
        moves.append(flip)
    return moves


def send_home(table, source):
    """`home_lift` is one card, or Spider's thirteen. An Ace goes to the first empty foundation, and so does a finished run."""
    cards = table.pile(source)
    count = table.variant.home_lift
    if source[0] == "foundation" or len(cards) < count or not cards[-1].face_up:
        return None
    for index in range(table.variant.foundation_count):
        if table.variant.goes_home(cards[len(cards) - count:],
                                   table.top(foundation(index))):
            return move_to(table, source, count, foundation(index))
    return None


def lift_finished_runs(table):
    """Every run this rule set takes off its own columns, LIFTED as it is found.

    It carries its moves out rather than only handing them back: one row off the stock can finish a run on more than one column, and the second is only visible with the first gone. One pass is enough — what a run uncovers cannot itself be finished.
    """
    if not table.variant.runs_leave_on_their_own:
        return []
    lifted = []
    for index in range(len(table.columns)):
        moves = send_home(table, column(index))
        if moves is None:
            continue
        for move in moves:
            move.apply(table)
        lifted.extend(moves)
    return lifted
