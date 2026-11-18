"""Responsive card rendering for the four historically distinct patience layouts.

Uses the original sprite atlas, toolbar, touch-selection and drag machinery.
"""
import pygame
from .extra_board import SpecialBoard, HIGHLIGHT
from .layout import CHROME_BAND, Layout
from .novel_games import NovelGame


def novel_layout(width, height, variant):
    lay = Layout(width, height, variant)
    usable = max(280, height - CHROME_BAND)
    if variant.name == 'Black Hole':
        max_width = (width - 70) // 10
        max_height = int(usable * .23 * 42 / 60)
    elif variant.name == 'Zodiac':
        max_width = (width - 55) // 13
        max_height = int(usable * .16 * 42 / 60)
    elif variant.name == 'Beleaguered Castle':
        max_width = (width - 60) // 9
        max_height = int(usable * .36 * 42 / 60)
    else:
        max_width = (width - 80) // 7
        max_height = int(usable * .45 * 42 / 60)
    lay.card_width = max(24, min(lay.card_width, max_width, max_height))
    lay.card_height = lay.card_width * 60 // 42
    return lay


class NovelBoard(SpecialBoard):
    def __init__(self, name):
        super().__init__('FreeCell')
        self.model = NovelGame(name)
        self.launch_points = {}

    def _put(self, screen, art, card, rect, ref=None, back=False):
        self._card(screen, art, card, rect, ref, back)
        if card is not None and not back:
            self.launch_points[card] = rect.topleft

    def _piles(self, screen, art, layout, piles, positions, maximum_span):
        cw, ch = layout.card_width, layout.card_height
        for i, pile in enumerate(piles):
            x, y = positions[i]
            if not pile:
                self._put(screen, art, None, pygame.Rect(x, y, cw, ch), ('t', i, 0))
                continue
            step = max(2, min(max(8, cw // 4), maximum_span // max(1, len(pile) - 1)))
            for j, card in enumerate(pile):
                # Only the exposed top card is selectable. Drawing the other
                # cards still supplies clear visual information about the pile.
                ref = ('t', i, j) if j == len(pile) - 1 else None
                self._put(screen, art, card,
                          pygame.Rect(x, y + j * step, cw, ch), ref)

    def _slots(self, screen, art, cards, refs, y, cw, ch, width, spacing=1.22):
        pitch = max(cw + 3, int(cw * spacing))
        count = len(cards)
        x0 = round((width - ((count - 1) * pitch + cw)) / 2)
        for i, card in enumerate(cards):
            self._put(screen, art, card, pygame.Rect(x0 + i * pitch, y, cw, ch), refs[i])

    def draw(self, screen, art, layout):
        self.regions = []
        m = self.model
        w, h = screen.get_size()
        cw, ch = layout.card_width, layout.card_height
        avail = h - CHROME_BAND
        top = CHROME_BAND + max(7, int(avail * .018))
        if m.is_blackhole:
            foundation_x = (w - cw) // 2
            self._put(screen, art, m.foundations[0][-1],
                      pygame.Rect(foundation_x, top, cw, ch), ('f', 0, 0))
            self._group_caption(screen, 'BLACK HOLE', foundation_x - cw // 3,
                                foundation_x + cw + cw // 3, top - 3, cw)
            pitch = min(int(cw * 1.18), (w - cw - 18) // 8)
            first_x = (w - (8 * pitch + cw)) // 2
            second_x = (w - (7 * pitch + cw)) // 2
            first_y = top + int(avail * .29)
            second_y = top + int(avail * .65)
            positions = ([(first_x + i * pitch, first_y) for i in range(9)] +
                         [(second_x + i * pitch, second_y) for i in range(8)])
            self._piles(screen, art, layout, m.tableau, positions,
                        max(18, int(avail * .11)))
        elif m.is_castle:
            self._group_caption(screen, 'CASTLE FOUNDATIONS', w // 3, 2 * w // 3,
                                top - 3, cw)
            self._slots(screen, art, [p[-1] for p in m.foundations],
                        [('f', i, 0) for i in range(4)], top, cw, ch, w)
            pitch = min(int(cw * 1.36), (w - cw - 20) // 7)
            x0 = (w - (7 * pitch + cw)) // 2
            positions = [(x0 + i * pitch, top + ch + int(avail * .07))
                         for i in range(8)]
            self._piles(screen, art, layout, m.tableau, positions,
                        max(15, h - positions[0][1] - ch - 8))
        elif m.is_birthday:
            x0 = max(10, (w - 7 * int(cw * 1.2)) // 2)
            pitch = int(cw * 1.2)
            stock = pygame.Rect(x0, top, cw, ch)
            waste = pygame.Rect(x0 + pitch, top, cw, ch)
            self._put(screen, art, None, stock, ('stock', 0, 0), bool(m.stock))
            if not m.stock and m.waste and m.passes < 4:
                self._slot_caption(screen, stock, 'REDEAL')
            self._put(screen, art, m.waste[-1] if m.waste else None,
                      waste, ('w', 0, 0))
            self._group_caption(screen, 'STOCK', stock.left, stock.right, top - 3, cw)
            self._group_caption(screen, 'WASTE', waste.left, waste.right, top - 3, cw)
            for i, pile in enumerate(m.foundations):
                rect = pygame.Rect(x0 + (i + 3) * pitch, top, cw, ch)
                self._put(screen, art, pile[-1], rect, ('f', i, 0))
            self._group_caption(screen, 'BIRTHDAY FOUNDATIONS', x0 + 3*pitch,
                                x0 + 6*pitch + cw, top - 3, cw)
            self._message(screen, f'Target {m.birthday_target}   |   Stock pass {m.passes} of 4',
                          top + ch + 35)
        elif m.is_zodiac:
            pitch = min(int(cw * 1.13), (w - cw - 20) // 11)
            x0 = (w - (11 * pitch + cw)) // 2
            upper_y = top + 15
            lower_y = top + int(avail * .70)
            positions = [(x0 + i * pitch, upper_y) for i in range(12)]
            positions += [(x0 + i * pitch, lower_y) for i in range(12)]
            equator_y = top + int(avail * .30)
            span = max(6, min(equator_y - upper_y - ch - 12,
                              h - lower_y - ch - 10))
            self._piles(screen, art, layout, m.tableau, positions, span)
            stock = pygame.Rect(x0, equator_y, cw, ch)
            waste = pygame.Rect(x0 + pitch, equator_y, cw, ch)
            self._put(screen, art, None, stock, ('stock', 0, 0), bool(m.stock))
            if not m.stock and m.waste:
                self._slot_caption(screen, stock, 'REDEAL')
            self._put(screen, art, m.waste[-1] if m.waste else None,
                      waste, ('w', 0, 0))
            # Six Equator cards fit to the right, with two in a second row.
            # Full eight-cell display uses the available width via 8 pitches:
            for i, card in enumerate(m.cells):
                rect = pygame.Rect(x0 + (i + 3) * pitch, equator_y, cw, ch)
                self._put(screen, art, card, rect, ('c', i, 0))
            self._group_caption(screen, 'EQUATOR', x0 + 3*pitch,
                                x0 + 10*pitch + cw, equator_y - 3, cw)
            foundation_y = top + int(avail * .50)
            self._slots(screen, art, [p[-1] if p else None for p in m.foundations],
                        [('f', i, 0) for i in range(8)], foundation_y, cw, ch, w,
                        spacing=1.13)
            self._group_caption(screen, 'FOUNDATIONS: ACES UP  /  KINGS DOWN',
                                x0 + pitch, x0 + 10*pitch + cw,
                                foundation_y - 3, cw)
        if m.message and not m.is_won():
            self._message(screen, m.message, max(CHROME_BAND - 22, 22))
        if m.is_zodiac and not m.message:
            self._message(screen,
                          'PHASE 2: build foundations' if m.phase_two else
                          'PHASE 1: pack the Zodiac and Equator',
                          max(CHROME_BAND - 22, 22))
        if self.dragging and self.press_ref is not None and self.pointer_xy is not None:
            cards = m._source(self.press_ref)
            if cards:
                x, y = self.pointer_xy
                screen.blit(art.of(cards[0]), (x - cw // 2, y - ch // 4))

    def _message(self, screen, message, center_y):
        w, h = screen.get_size()
        font = pygame.font.Font(None, max(18, min(29, h // 32)))
        image = font.render(message, True, (229, 246, 230))
        if image.get_width() > w - 30:
            image = pygame.transform.smoothscale(image, (w - 30, image.get_height()))
        rect = image.get_rect(center=(w // 2, center_y))
        shadow = pygame.Surface((rect.width + 18, rect.height + 7), pygame.SRCALPHA)
        shadow.fill((6, 38, 29, 215))
        screen.blit(shadow, (rect.left - 9, rect.top - 3))
        screen.blit(image, rect)

    def release(self, point):
        if self.model.is_blackhole and self.press_ref is not None and not self.dragging:
            source = self.press_ref
            if source[0] == 't':
                self.press_ref = self.press_xy = self.pointer_xy = None
                self.selected = None
                self.model.message = ''
                return 'move' if self.model.move(source, ('f', 0, 0)) else None
        return super().release(point)

    def victory_launches(self):
        return [(card, self.launch_points.get(card, (0, 0)))
                for pile in self.model.foundations for card in pile]
