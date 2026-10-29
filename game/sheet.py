"""The card sheet, and how it is cut.

`assets/sprites.png` is thirteen columns by five rows of 252 x 360 cells: rows are the suits in bridge order, columns are the ranks so `column = rank - 1`, and row 4 column 0 is the back.
"""
import os

import pygame

from .cards import HEARTS, RANKS, SPADES, SUITS

SHEET_NAME = "sprites.png"
CELL_WIDTH = 252
CELL_HEIGHT = 360
EXTRAS_ROW = 4
BACK_COLUMN = 0

# The deck's own printed corner, where the back's pattern and the courts' frames stop.
CORNER_RADIUS_FRACTION = 0.05

# A card lying on a card needs a hairline; the deck draws no outer border.
EDGE_COLOUR = (0, 0, 0, 70)
EDGE_FRACTION = 0.007  # of the card's width

# Not on the sheet: this deck draws no such card.
SLOT_FILL = (255, 255, 255, 26)
SLOT_EDGE = (255, 255, 255, 96)
SLOT_EDGE_FRACTION = 0.016

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _round_corners(card, radius):
    """On the card at its final size, which is what makes the arc a true circle at any size."""
    width, height = card.get_size()
    corners = ((0, 0, 1, 1), (width - 1, 0, -1, 1),
               (0, height - 1, 1, -1), (width - 1, height - 1, -1, -1))
    for corner_x, corner_y, step_x, step_y in corners:
        for i in range(radius):
            for j in range(radius):
                across = radius - (i + 0.5)
                down = radius - (j + 0.5)
                distance = (across * across + down * down) ** 0.5
                if distance <= radius - 0.5:
                    continue
                point = (corner_x + step_x * i, corner_y + step_y * j)
                colour = card.get_at(point)
                if distance >= radius + 0.5:
                    colour.a = 0
                elif colour.a:
                    # never rounds away to nothing, so the outline stays geometry
                    colour.a = max(1, int(colour.a * (radius + 0.5 - distance)))
                card.set_at(point, colour)


def _draw_edge(card, radius, width):
    """Drawn before the corners are carved: `pygame.draw.rect` rounds in whole pixels, and carving second trims what it left proud of the true arc."""
    edge = pygame.Surface(card.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(edge, EDGE_COLOUR, edge.get_rect(),
                     width=width, border_radius=radius)
    card.blit(edge, (0, 0))


def _empty_slot(size, radius):
    """A slot, not a faded card back: a face-down card is a real thing on this table."""
    slot = pygame.Surface(size, pygame.SRCALPHA)
    slot.fill(SLOT_FILL)
    pygame.draw.rect(slot, SLOT_EDGE, slot.get_rect(),
                     width=max(1, round(size[0] * SLOT_EDGE_FRACTION)),
                     border_radius=radius)
    _round_corners(slot, radius)
    return slot


class Art:
    def __init__(self, card_width, card_height):
        # `convert`/`convert_alpha` need a display, so this cannot happen at import time.
        sheet = pygame.image.load(os.path.join(ASSETS_DIR, SHEET_NAME))
        size = (card_width, card_height)
        radius = max(1, round(card_width * CORNER_RADIUS_FRACTION))
        edge_width = max(1, round(card_width * EDGE_FRACTION))

        def cut(column, row):
            # One cell at a time, so the whole sheet is never held at four bytes a pixel.
            cell = sheet.subsurface(
                pygame.Rect(column * CELL_WIDTH, row * CELL_HEIGHT,
                            CELL_WIDTH, CELL_HEIGHT)).convert()
            card = pygame.transform.smoothscale(cell, size).convert_alpha()
            _draw_edge(card, radius, edge_width)
            _round_corners(card, radius)
            return card

        self.faces = {(suit, rank): cut(rank - 1, suit)
                      for suit in SUITS for rank in RANKS}
        self.back = cut(BACK_COLUMN, EXTRAS_ROW)
        self.slot = _empty_slot(size, radius)

    def of(self, card):
        return self.faces[(card.suit, card.rank)] if card.face_up else self.back
