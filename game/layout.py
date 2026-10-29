"""Turning the canvas into a table. Everything comes from the size `set_mode` returns and from the rule set's column count, so a `Layout` is measured per deal."""
import pygame
import sys

from .rules import KLONDIKE
from .table import STOCK, WASTE, foundation

CARD_ART_WIDTH = 42
CARD_ART_HEIGHT = 60
MIN_CARD_WIDTH = CARD_ART_WIDTH  # a tiny canvas still gets a table

# The app's buttons sit across the top of the screen; nothing is drawn under them.
IS_WEB = sys.platform == 'emscripten'
CHROME_BAND = 78 if IS_WEB else 180
CHROME_LEADING = 12 if IS_WEB else 180
CHROME_TRAILING = 12 if IS_WEB else 348

# Everything below is a length in the 42 x 60 box, and goes through `scaled`.
COLUMN_GAP = 10
SIDE_MARGIN = 8
TOP_GAP = 8  # between the chrome band and the row of piles
ROW_GAP = 12  # between that row and the tops of the columns
BOTTOM_MARGIN = 8
MIN_TABLEAU_HEIGHT = 2 * CARD_ART_HEIGHT  # a column needs somewhere to fan

# What the table costs down; across depends on the rule set's column count.
TABLE_ART_HEIGHT = (TOP_GAP + CARD_ART_HEIGHT + ROW_GAP + MIN_TABLEAU_HEIGHT
                    + BOTTOM_MARGIN)


def row_art_width(column_count):
    return (column_count * CARD_ART_WIDTH + (column_count - 1) * COLUMN_GAP
            + 2 * SIDE_MARGIN)

# Spare width goes into the gaps first, up to this much of a card.
MAX_COLUMN_GAP_NUMERATOR = 3
MAX_COLUMN_GAP_DENOMINATOR = 4

# 14 of a card's 60 rows clears the rank in its corner; a face-down card only has to be countable.
FACE_UP_FAN = 14
FACE_DOWN_FAN = 7
MIN_FAN = 2

BUTTON_BAND_FRACTION = 1, 2  # of the chrome band's height
BUTTON_ASPECT = 8, 5
VARIANT_BUTTON_ASPECT = 3, 1  # wider: a name, four dots and the arrow
MIN_BUTTON_HEIGHT = 38 if IS_WEB else 40

PICKER_ROW_ASPECT = 5  # plate-heights across
PICKER_PADDING_DIVISOR = 10
PICKER_OVERLAP_DIVISOR = 6  # how far the list tucks up under its plate
PICKER_CORNER_DIVISOR = 4
PICKER_INSET_DIVISOR = 3


class Layout:
    """Where every pile is, how far each column fans, and what a touch landed on."""

    def __init__(self, width, height, variant=None):
        variant = variant or KLONDIKE
        self.width = width
        self.height = height
        self.column_count = variant.column_count
        self.foundation_count = variant.foundation_count
        # The foundations take the LAST slots of the top row.
        self.first_foundation_column = self.column_count - self.foundation_count

        # A pile this rule set has not got is left out rather than drawn dead.
        self.row_piles = (([STOCK] if variant.has_stock else [])
                          + ([WASTE] if variant.has_waste else [])
                          + [foundation(index) for index in range(self.foundation_count)])

        # The largest card that fits both ways — any width, not a whole multiple.
        self.row_art_width = row_art_width(self.column_count)
        across = width * CARD_ART_WIDTH // self.row_art_width
        down = (height - CHROME_BAND) * CARD_ART_WIDTH // TABLE_ART_HEIGHT
        self.card_width = max(MIN_CARD_WIDTH, min(across, down))
        self.card_height = self.card_width * CARD_ART_HEIGHT // CARD_ART_WIDTH

        spare = max(0, width - self.column_count * self.card_width)
        # One share per gap between columns, and one for the margin at each end.
        self.column_gap = min(spare // (self.column_count + 1),
                              self.card_width * MAX_COLUMN_GAP_NUMERATOR
                              // MAX_COLUMN_GAP_DENOMINATOR)
        self.column_pitch = self.card_width + self.column_gap
        row_width = (self.column_count * self.card_width
                     + (self.column_count - 1) * self.column_gap)
        self.left = (width - row_width) // 2

        self.row_top = CHROME_BAND + self.scaled(TOP_GAP)
        self.tableau_top = self.row_top + self.card_height + self.scaled(ROW_GAP)
        self.tableau_height = max(self.card_height,
                                  height - self.scaled(BOTTOM_MARGIN) - self.tableau_top)

        self.undo_button, self.new_button, self.variant_button, self.rules_button = self._buttons()
        self.button_font_height = max(12, self.undo_button.height // 2)

    def scaled(self, art_length):
        return art_length * self.card_width // CARD_ART_WIDTH

    # -- the buttons the game draws for itself --

    def _buttons(self):
        """Three plates, centred in the strip the app's buttons leave free."""
        free_left = CHROME_LEADING
        free_width = max(1, self.width - CHROME_LEADING - CHROME_TRAILING)

        numerator, denominator = BUTTON_BAND_FRACTION
        height = max(MIN_BUTTON_HEIGHT, CHROME_BAND * numerator // denominator)
        if _plate_row_width(height, include_rules=True) > free_width:
            # Shrink the row rather than let a plate slide under a button.
            height = max(1, height * free_width // _plate_row_width(height, include_rules=True))
        width = _by(height, BUTTON_ASPECT)
        gap = height // 2

        left = free_left + (free_width - _plate_row_width(height, include_rules=True)) // 2
        top = (CHROME_BAND - height) // 2
        variant_left = left + 2 * (width + gap)
        return (pygame.Rect(left, top, width, height),
                pygame.Rect(left + width + gap, top, width, height),
                pygame.Rect(variant_left, top,
                            _by(height, VARIANT_BUTTON_ASPECT), height),
                pygame.Rect(variant_left + _by(height, VARIANT_BUTTON_ASPECT) + gap,
                            top, width, height))

    # -- the list of rule sets that plate opens --

    def picker_row_height(self, count):
        """Twelve existing choices keep their original single-column menu."""
        padding = self._picker_padding()
        if count > 12:
            rows = (count + 1) // 2
            room = self.height - max(96, self.variant_button.bottom) - 2 * padding - 10
            return max(22, min(self.variant_button.height, room // rows))
        room = self.height - self.picker_top - 2 * padding
        return max(1, min(self.variant_button.height, room // max(1, count)))

    @property
    def picker_width(self):
        plate = self.variant_button
        natural = (max(plate.width, plate.height * PICKER_ROW_ASPECT)
                   + 2 * self._picker_padding())
        if self.width < 1000:
            natural = max(natural, self.width * 53 // 100)
        return min(self.width, natural)

    @property
    def picker_left(self):
        return max(0, min(self.variant_button.left, self.width - self.picker_width))

    def picker_panel(self, count):
        if count > 12:
            width = min(self.width - 12, max(480, min(830, self.picker_width * 2)))
            height = ((count + 1) // 2) * self.picker_row_height(count) + 2 * self._picker_padding()
            panel = pygame.Rect((self.width - width) // 2,
                                max(80, self.variant_button.bottom - 9), width, height)
            panel.top = max(0, min(panel.top, self.height - height))
            return panel
        width = self.picker_width
        height = count * self.picker_row_height(count) + 2 * self._picker_padding()
        panel = pygame.Rect(self.picker_left, self.picker_top, width, height)
        panel.top = max(0, min(panel.top, self.height - height))
        return panel

    def picker_rows(self, count):
        panel = self.picker_panel(count)
        padding = self._picker_padding()
        height = self.picker_row_height(count)
        if count > 12:
            col_gap = max(5, padding)
            col_width = (panel.width - 2 * padding - col_gap) // 2
            return [pygame.Rect(panel.left + padding + (i % 2) * (col_width + col_gap),
                                panel.top + padding + (i // 2) * height,
                                col_width, height) for i in range(count)]
        return [pygame.Rect(panel.left + padding,
                            panel.top + padding + index * height,
                            panel.width - 2 * padding, height)
                for index in range(count)]

    def picker_row_at(self, point, count):
        for index, rect in enumerate(self.picker_rows(count)):
            if rect.collidepoint(point):
                return index
        return None

    @property
    def picker_top(self):
        """Tucked up inside its own plate — but not at either end of the band, where a row would land behind one of the app's buttons."""
        plate = self.variant_button
        tucked = max(0, plate.bottom - plate.height // PICKER_OVERLAP_DIVISOR)
        left = self.picker_left
        if left < CHROME_LEADING or left + self.picker_width > self.width - CHROME_TRAILING:
            return max(tucked, CHROME_BAND)
        return tucked

    @property
    def picker_corner(self):
        return max(2, self.variant_button.height // PICKER_CORNER_DIVISOR)

    @property
    def picker_inset(self):
        return max(3, self.variant_button.height // PICKER_INSET_DIVISOR)

    def _picker_padding(self):
        return max(2, self.variant_button.height // PICKER_PADDING_DIVISOR)

    # -- where the piles are --

    def column_left(self, index):
        return self.left + index * self.column_pitch

    def pile_rect(self, identifier):
        """Also where its empty slot is drawn."""
        kind, index = identifier
        if kind == "stock":
            return self._row_rect(0)
        if kind == "waste":
            return self._row_rect(1)
        if kind == "foundation":
            return self._row_rect(self.first_foundation_column + index)
        return pygame.Rect(self.column_left(index), self.tableau_top,
                           self.card_width, self.card_height)

    def _row_rect(self, index):
        return pygame.Rect(self.column_left(index), self.row_top,
                           self.card_width, self.card_height)

    def fan_offsets(self, cards):
        """How far down the column each card sits, first card first.

        A column too long for its room has both step sizes squeezed in proportion until it fits, and past even the floor rather than run off the bottom of the canvas: a card nobody can reach cannot be played. Drawing and hit-testing both call this.
        """
        if not cards:
            return []
        down = self.scaled(FACE_DOWN_FAN)
        up = self.scaled(FACE_UP_FAN)
        room = self.tableau_height - self.card_height
        span = _fan_span(cards, down, up)
        if span > room:
            floor = self.scaled(MIN_FAN)
            down = max(floor, down * room // span)
            up = max(floor, up * room // span)
            reach = self.height - self.tableau_top - self.card_height
            squeezed = _fan_span(cards, down, up)
            if squeezed > reach:
                down = max(1, down * reach // squeezed)
                up = max(1, up * reach // squeezed)
        offsets = []
        y = self.tableau_top
        for card in cards:
            offsets.append(y)
            y += up if card.face_up else down
        return offsets

    def card_rect(self, identifier, index, cards):
        if identifier[0] != "tableau":
            return self.pile_rect(identifier)
        rect = self.pile_rect(identifier)
        rect.top = self.fan_offsets(cards)[index]
        return rect

    def column_extent(self, index, cards):
        """Slot included."""
        rect = self.pile_rect(("tableau", index))
        if cards:
            rect.height = self.fan_offsets(cards)[-1] + self.card_height - rect.top
        return rect

    # -- what a touch landed on --

    def button_at(self, point):
        if self.undo_button.collidepoint(point):
            return "undo"
        if self.new_button.collidepoint(point):
            return "new"
        if self.variant_button.collidepoint(point):
            return "variant"
        if self.rules_button.collidepoint(point):
            return "rules"
        return None

    def card_at(self, table, point):
        """An empty pile answers with an index of -1, so a tap on the empty stock is still a tap on something."""
        for index in range(len(table.columns)):
            cards = table.columns[index]
            identifier = ("tableau", index)
            offsets = self.fan_offsets(cards)
            for card_index in range(len(cards) - 1, -1, -1):
                rect = self.pile_rect(identifier)
                rect.top = offsets[card_index]
                if rect.collidepoint(point):
                    return identifier, card_index
            if not cards and self.pile_rect(identifier).collidepoint(point):
                return identifier, -1

        for identifier in self.row_piles:
            if self.pile_rect(identifier).collidepoint(point):
                return identifier, len(table.pile(identifier)) - 1
        return None

    def drop_target(self, table, rect):
        """Overlap rather than the finger's position, so a card released a little short still goes where it meant to."""
        best, best_area = None, 0
        targets = [("foundation", index) for index in range(self.foundation_count)]
        for identifier in targets:
            area = _overlap(rect, self.pile_rect(identifier))
            if area > best_area:
                best, best_area = identifier, area
        for index in range(len(table.columns)):
            area = _overlap(rect, self.column_extent(index, table.columns[index]))
            if area > best_area:
                best, best_area = ("tableau", index), area
        return best


def _fan_span(cards, down, up):
    return sum(up if card.face_up else down for card in cards[:-1])


def _by(length, fraction):
    numerator, denominator = fraction
    return length * numerator // denominator


def _plate_row_width(height, include_rules=False):
    plates = 3 if include_rules else 2
    gaps = 3 if include_rules else 2
    return (plates * _by(height, BUTTON_ASPECT)
            + _by(height, VARIANT_BUTTON_ASPECT) + gaps * (height // 2))


def _overlap(first, second):
    clipped = first.clip(second)
    return clipped.width * clipped.height
