"""Sprite-based layouts and touch UX for additional nonstandard boards.

Isolated from the existing twelve implementations: the shared UI delegates to
this only when one of MORE_GAMES is selected. All cards use the existing Art.
"""
import pygame
from .extra_board import SpecialBoard, HIGHLIGHT, LEGAL
from .more_games import MoreGame
from .layout import CHROME_BAND, Layout


def more_layout(width, height, variant):
    lay = Layout(width, height, variant)
    if variant.name == 'Relaxed Pyramid':
        # Seven partially overlapping rows, 28 cards total.
        w_by_height = int((height - CHROME_BAND - 36) * 42 / (60 * (1 + 6 * .40)))
        lay.card_width = max(30, min(lay.card_width, w_by_height))
    elif variant.name == 'TriPeaks':
        w_by_height = int((height - CHROME_BAND - 40) * 42 / (60 * (1 + 3 * .53)))
        lay.card_width = max(30, min(lay.card_width, w_by_height))
    lay.card_height = lay.card_width * 60 // 42
    if variant.name in ('Golf', 'Scorpion II'):
        lay.row_top = CHROME_BAND + max(7, lay.card_width // 12)
        lay.tableau_top = lay.row_top + lay.card_height + max(7, lay.card_width // 8)
    return lay


class MoreBoard(SpecialBoard):
    def __init__(self, name):
        super().__init__('FreeCell')  # initialise UI-only fields; replace model below
        self.model = MoreGame(name)
        self.launch_points = {}

    def _put(self, screen, art, card, rect, ref, back=False):
        self._card(screen, art, card, rect, ref, back)
        if card is not None and not back:
            self.launch_points[card] = rect.topleft

    def draw(self, screen, art, layout):
        self.regions = []
        m = self.model
        w, h = screen.get_size()
        cw, ch = layout.card_width, layout.card_height
        if m.is_golf:
            # Same visual convention as the original seven-column games.
            stock = pygame.Rect(layout.column_left(0), layout.row_top, cw, ch)
            discard = pygame.Rect(layout.column_left(1), layout.row_top, cw, ch)
            self._put(screen, art, None, stock, ('stock', 0, 0), bool(m.stock))
            self._put(screen, art, m.waste[-1], discard, None)
            self._group_caption(screen, 'DRAW', stock.x, stock.right, stock.y - 3, cw)
            self._group_caption(screen, 'DISCARD', discard.x, discard.right, discard.y - 3, cw)
            for i, pile in enumerate(m.tableau):
                left = layout.column_left(i)
                top = layout.tableau_top
                step = min(max(15, cw * 32 // 100),
                           max(1, (h - ch - top - 8) // 4))
                if not pile:
                    self._put(screen, art, None, pygame.Rect(left, top, cw, ch), None)
                for j, card in enumerate(pile):
                    ref = ('t', i, j) if j == len(pile) - 1 else None
                    rect = pygame.Rect(left, top + j * step, cw, ch)
                    self._put(screen, art, card, rect, ref)
                    if ref == self.selected:
                        pygame.draw.rect(screen, HIGHLIGHT, rect, 3,
                                         border_radius=max(3, cw // 20))
        elif m.is_scorpion:
            stock = pygame.Rect(layout.column_left(0), layout.row_top, cw, ch)
            self._put(screen, art, None, stock, ('stock', 0, 0), bool(m.stock))
            self._group_caption(screen, 'LAST THREE', stock.left, stock.right,
                                stock.y - 3, cw)
            for i, pile in enumerate(m.tableau):
                left = layout.column_left(i)
                top = layout.tableau_top
                if not pile:
                    self._put(screen, art, None, pygame.Rect(left, top, cw, ch), ('t', i, 0))
                    continue
                step = min(max(11, cw // 4), max(1, (h - top - ch - 9) // max(1, len(pile)-1)))
                for j, card in enumerate(pile):
                    rect = pygame.Rect(left, top + j * step, cw, ch)
                    if j < m.down[i]:
                        self._put(screen, art, None, rect, None, back=True)
                    else:
                        self._put(screen, art, card, rect, ('t', i, j))
                        if self.selected == ('t', i, j):
                            pygame.draw.rect(screen, HIGHLIGHT, rect, 3,
                                             border_radius=max(3, cw // 20))
        else:
            # Geometry independent of the normal fan tableau. The bottom row
            # overlaps rows above it, so top-down rendering gives proper depth.
            if m.is_tripeaks:
                pitch = cw * .91
                base_left = (w - (9 * pitch + cw)) / 2
                top = CHROME_BAND + 14
                step_y = int(ch * .53)
                positions = []
                for p in range(3):
                    positions.append((base_left + (1.5 + 3*p)*pitch, top))
                for p in range(3):
                    for k in range(2):
                        positions.append((base_left + (1 + 3*p + k)*pitch, top + step_y))
                for k in range(9):
                    positions.append((base_left + (.5 + k)*pitch, top + 2*step_y))
                for k in range(10):
                    positions.append((base_left + k*pitch, top + 3*step_y))
            else:
                pitch = cw * .87
                base_left = (w - (6 * pitch + cw)) / 2
                top = CHROME_BAND + 12
                step_y = int(ch * .40)
                positions = []
                for row in range(7):
                    for k in range(row + 1):
                        positions.append((base_left + ((6-row)*.5 + k)*pitch,
                                          top + row*step_y))
            for idx, card in enumerate(m.board):
                if card is None:
                    continue
                x, y = positions[idx]
                exposed = m.exposed(idx)
                # TriPeaks concealed cards use the original card back; Pyramid
                # cards are all face up, but can't be selected until uncovered.
                back = m.is_tripeaks and not exposed
                rect = pygame.Rect(round(x), round(y), cw, ch)
                ref = ('b', idx, 0) if exposed else None
                self._put(screen, art, card if not back else None, rect, ref, back)
                if ref == self.selected:
                    pygame.draw.rect(screen, HIGHLIGHT, rect, 3,
                                     border_radius=max(3, cw // 20))
            # Stacks are to the right of the three peaks/pyramid, never over cards.
            stock = pygame.Rect(max(9, w - cw * 2 - max(25, cw//3)),
                                CHROME_BAND + 7, cw, ch)
            waste = pygame.Rect(stock.right + max(10, cw//7), stock.y, cw, ch)
            if waste.right > w - 5:
                stock.x = max(5, w - 2*cw - 18)
                waste.x = stock.right + 8
            self._put(screen, art, None, stock, ('stock', 0, 0), bool(m.stock))
            if m.is_pyramid and not m.stock and m.redeals_remaining and m.waste:
                self._slot_caption(screen, stock, 'REDEAL')
            self._group_caption(screen, 'STOCK', stock.x, stock.right, stock.y - 3, cw)
            self._put(screen, art, m.waste[-1] if m.waste else None,
                      waste, ('w', 0, 0) if m.is_pyramid and m.waste else None)
            self._group_caption(screen, 'PAIR' if m.is_pyramid else 'DISCARD',
                                waste.x, waste.right, waste.y - 3, cw)
            if m.is_pyramid and self.selected == ('w', 0, 0):
                pygame.draw.rect(screen, HIGHLIGHT, waste, 3, border_radius=max(3,cw//20))

        # A short, non-obscuring message immediately below the toolbar.
        if m.message and not m.is_won():
            font = pygame.font.Font(None, max(19, min(30, h//28)))
            img = font.render(m.message[:80], True, (232, 242, 232))
            bg = pygame.Surface((img.get_width()+20, img.get_height()+8), pygame.SRCALPHA)
            bg.fill((6, 39, 30, 225))
            r = bg.get_rect(center=(w//2, CHROME_BAND-11))
            screen.blit(bg, r)
            screen.blit(img, img.get_rect(center=r.center))
        if self.dragging and self.press_ref is not None and self.pointer_xy is not None:
            cards = m._source(self.press_ref)
            if cards:
                x = self.pointer_xy[0] - cw//2
                y = self.pointer_xy[1] - ch//4
                step = max(8, min(cw//4, (h - y - ch)//max(1,len(cards))))
                for i, card in enumerate(cards):
                    screen.blit(art.of(card), (x, y + i*step))

    def release(self, point):
        source = self.press_ref
        self.press_ref = self.press_xy = self.pointer_xy = None
        target = self.hit(point)
        was_drag = self.dragging
        self.dragging = False
        m = self.model
        if source is None:
            self.selected = None if target is None else self.selected
            return None
        if source[0] == 'stock':
            self.selected = None
            return 'draw' if m.draw() else None
        if was_drag:
            first = source
            second = target
        else:
            if m.is_golf or m.is_tripeaks:
                self.selected = None
                return 'move' if m.move(source, ('w', 0, 0)) else None
            if m.is_pyramid and m._source(source) and m._source(source)[0].rank == 13:
                self.selected = None
                return 'move' if m.move(source, ('discard', 0, 0)) else None
            if self.selected and self.selected != target:
                first, second = self.selected, target
            else:
                if source[0] in ('b', 't', 'w') and m._source(source):
                    self.selected = source
                else:
                    self.selected = None
                return None
        if first and second and m.move(first, second):
            self.selected = None
            return 'move'
        # Scorpion also lets a King packet move into an empty column with tap-to-select.
        if m._source(source):
            self.selected = source
        m.message = 'That move is not allowed'
        return None

    def victory_launches(self):
        m = self.model
        if m.is_golf or m.is_tripeaks:
            return [(c, self.launch_points.get(c, (0, 0))) for c in m.waste]
        if m.is_pyramid:
            return [(c, self.launch_points.get(c, (0, 0))) for c in m.removed]
        return [(c, self.launch_points.get(c, (0, 0)))
                for pile in m.tableau for c in pile]
