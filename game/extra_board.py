"""Special-board geometry and touch interactions for the original six additional variants and two related variants.

All cards use the SAME Art sprite sheet as Klondike, the SAME Painter buttons,
its dropdown and winning panel. Only the special pile arrangements live here.
The original Table, Drag and Flight implementations are not modified.
"""
import pygame

from .extra_games import ExtraGame
from .layout import CHROME_BAND, CHROME_TRAILING, Layout
from .paint import COLOR_TABLE, COLOR_TEXT

HIGHLIGHT = (255, 207, 64)
LEGAL = (113, 228, 170)
BLOCKED = (116, 137, 125)
SUIT_ABBREV = "SHDC"
RANK_HINT = ("", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")


def special_layout(width, height, variant):
    """Use the classic responsive layout, accounting for the extra top cells/grids."""
    lay = Layout(width, height, variant)
    name = variant.name
    if name in ("Addiction Solitaire", "Maze Solitaire"):
        cols, rows = (13, 4) if name == "Addiction Solitaire" else (9, 6)
        avail_w = max(1, width - 28)
        avail_h = max(1, height - CHROME_BAND - 30)
        card_w = min(int(avail_w / (cols * 1.015)), int(avail_h / rows * 42 / 60))
        lay.card_width = max(18, card_w)
        lay.card_height = lay.card_width * 60 // 42
    elif name == "Penguin":
        # Preserve existing Penguin sizing and play area.
        lay.card_width = max(42, min(lay.card_width, (width - 24) // 12))
        lay.card_height = lay.card_width * 60 // 42
    elif name == "Eight Off":
        # Twelve top-row slots: eight reserve cells and four foundations.
        # Reserve 12 px margins and at least four px between each slot.
        fit_width = (width - 24 - 11 * 4) // 12
        lay.card_width = min(lay.card_width, max(18, fit_width))
        lay.card_height = lay.card_width * 60 // 42
    if name == "Addiction Solitaire":
        # Addiction alone has a fifth toolbar control. Reflow all FIVE plates
        # in the original protected toolbar corridor; the old approach put
        # Shuffle beneath the large Juno CLOSE button and status banner.
        available = max(1, width - 180 - CHROME_TRAILING)
        def span(height):
            return 4 * (height * 8 // 5) + 3 * height + 4 * (height // 2)
        button_h = lay.undo_button.height
        while button_h > 24 and span(button_h) > available:
            button_h -= 1
        button_w = button_h * 8 // 5
        space = button_h // 2
        left = 180 + max(0, (available - span(button_h)) // 2)
        top = (CHROME_BAND - button_h) // 2
        lay.undo_button = pygame.Rect(left, top, button_w, button_h)
        left += button_w + space
        lay.new_button = pygame.Rect(left, top, button_w, button_h)
        left += button_w + space
        lay.variant_button = pygame.Rect(left, top, 3 * button_h, button_h)
        left += 3 * button_h + space
        lay.rules_button = pygame.Rect(left, top, button_w, button_h)
        left += button_w + space
        lay.reshuffle_button = pygame.Rect(left, top, button_w, button_h)
        lay.button_font_height = max(12, button_h // 2)
    if name not in ("Addiction Solitaire", "Maze Solitaire"):
        col_count = (8 if name in ("FreeCell", "Eight Off", "Old Patience / Sir Tommy")
                     else 7)
        lay.column_count = col_count
        avail = max(0, width - col_count * lay.card_width)
        lay.column_gap = min(avail // (col_count + 1), lay.card_width * 3 // 4)
        lay.column_pitch = lay.card_width + lay.column_gap
        lay.left = (width - col_count * lay.card_width - (col_count - 1) * lay.column_gap) // 2
        lay.row_top = CHROME_BAND + max(6, lay.card_width // 12)
        lay.tableau_top = lay.row_top + lay.card_height + max(9, lay.card_width // 10)
        lay.tableau_height = height - lay.tableau_top - 10
    return lay


class SpecialBoard:
    """Drawing and touch mapping; the ExtraGame model owns ALL legality and undo."""

    def __init__(self, name):
        self.model = ExtraGame(name)
        self.selected = None
        self.press_ref = None
        self.press_xy = None
        self.pointer_xy = None
        self.dragging = False
        self.regions = []
        self.last_tap = None
        self.hint_gap = None

    def reset(self):
        self.model.new_game()
        self.selected = self.press_ref = self.press_xy = self.pointer_xy = None
        self.dragging = False
        self.hint_gap = None

    def _add(self, rect, ref):
        self.regions.append((rect.copy(), ref))

    def _card(self, screen, art, card, rect, ref, back=False):
        if back:
            surf = art.back
        elif card is None:
            surf = art.slot
        else:
            surf = art.of(card)
        screen.blit(surf, rect)
        if card is None and ref is not None and ref[0] in ("c", "f", "t", "p", "w", "stock"):
            if ref[0] == "c":
                caption = "FLIP" if self.model.is_penguin else "FREE"
            elif ref[0] == "f":
                caption = "HOME"
            elif ref[0] == "stock":
                caption = "DRAW"
            elif ref[0] == "w":
                caption = "WASTE"
            elif ref[0] == "p":
                caption = "DEALT"
            elif self.model.is_tommy:
                caption = "WASTE"
            else:
                caption = "EMPTY"
            self._slot_caption(screen, rect, caption)
        if ref == self.selected:
            pygame.draw.rect(screen, HIGHLIGHT, rect, width=max(2, rect.width // 48),
                             border_radius=max(3, rect.width // 20))
        if ref is not None:
            self._add(rect, ref)

    def _slot_caption(self, screen, rect, label):
        """Procedural slot marker: no extra artwork or missing Unicode glyphs."""
        font = pygame.font.Font(None, max(11, min(23, rect.width // 5)))
        ink = font.render(label, True, (204, 233, 219))
        if ink.get_width() > rect.width - 8:
            ink = pygame.transform.smoothscale(
                ink, (max(1, rect.width - 8), ink.get_height()))
        screen.blit(ink, ink.get_rect(center=rect.center))

    def _group_caption(self, screen, text, left, right, baseline, card_width):
        font = pygame.font.Font(None, max(14, min(25, card_width // 6)))
        image = font.render(text, True, COLOR_TEXT)
        if image.get_width() > right - left:
            image = pygame.transform.smoothscale(
                image, (max(1, right - left), image.get_height()))
        screen.blit(image, image.get_rect(centerx=(left + right) // 2,
                                          bottom=baseline))

    def _column(self, screen, art, layout, pile, idx, left, top):
        size = (layout.card_width, layout.card_height)
        if not pile:
            self._card(screen, art, None, pygame.Rect((left, top), size), ("t", idx, 0))
            return
        # Fans always remain reachable, even when columns become very long.
        room = max(1, layout.height - top - layout.card_height - 12)
        step = min(max(5, layout.card_width // 3), room // max(1, len(pile) - 1))
        step = max(1, step)
        for j, card in enumerate(pile):
            rect = pygame.Rect(left, top + j * step, *size)
            self._card(screen, art, card, rect, ("t", idx, j))

    def draw(self, screen, art, layout):
        self.regions = []
        m = self.model
        w, h = screen.get_size()
        cw, ch = layout.card_width, layout.card_height
        if m.is_grid:
            cols, rows = (13, 4) if m.is_addiction else (9, 6)
            gap = max(2, min(8, int((w - cols * cw) / max(1, cols - 1))))
            pitch_x = cw + gap
            pitch_y = ch + max(2, min(6, (h - CHROME_BAND - rows * ch - 20) // max(1, rows - 1)))
            left = (w - ((cols - 1) * pitch_x + cw)) // 2
            top = CHROME_BAND + max(6, (h - CHROME_BAND - ((rows - 1) * pitch_y + ch)) // 2)
            legal = m.grid_legal_moves()
            legal_sources = {src for src, _ in legal}
            legal_gaps = {dst for _, dst in legal}
            if self.selected is not None and self.selected[0] == "g":
                if m.grid[self.selected[1]] is None:
                    selected_targets = {src for src, dst in legal
                                        if dst == self.selected[1]}
                else:
                    selected_targets = {dst for src, dst in legal
                                        if src == self.selected[1]}
            else:
                selected_targets = set()
            for n, card in enumerate(m.grid):
                rect = pygame.Rect(left + (n % cols) * pitch_x,
                                   top + (n // cols) * pitch_y, cw, ch)
                self._card(screen, art, card, rect, ("g", n, 0))
                if card is None:
                    # Immediately distinguish a playable gap from a blocked one.
                    colour = LEGAL if n in legal_gaps else BLOCKED
                    pygame.draw.rect(screen, colour, rect.inflate(-4, -4),
                                     max(2, cw // 37), border_radius=max(2, cw // 18))
                    count = sum(1 for _, dst in legal if dst == n)
                    self._slot_caption(screen, rect, str(count) if count else "X")
                if (n in selected_targets or
                        (self.selected is None and n in legal_sources and card is not None)):
                    colour = HIGHLIGHT if n in selected_targets else LEGAL
                    pygame.draw.rect(screen, colour, rect.inflate(-3, -3),
                                     max(2, cw // 35), border_radius=max(2, cw // 18))
        else:
            top_y = layout.row_top
            tableau_y = layout.tableau_top
            if m.is_eightoff:
                slots = 12
                gap = max(4, min(cw // 7, (w - slots * cw) // 13))
                start_x = max(4, (w - (slots * cw + (slots - 1) * gap)) // 2)
                self._group_caption(screen, "RESERVE CELLS", start_x,
                                    start_x + 8 * cw + 7 * gap, top_y - 3, cw)
                self._group_caption(screen, "FOUNDATIONS",
                                    start_x + 8 * (cw + gap),
                                    start_x + 11 * (cw + gap) + cw,
                                    top_y - 3, cw)
                for i in range(8):
                    r = pygame.Rect(start_x + i * (cw + gap), top_y, cw, ch)
                    self._card(screen, art, m.cells[i], r, ("c", i, 0))
                for i in range(4):
                    r = pygame.Rect(start_x + (i + 8) * (cw + gap), top_y, cw, ch)
                    pile = m.foundations[i]
                    self._card(screen, art, pile[-1] if pile else None, r, ("f", i, 0))
            elif m.is_freecell:
                self._group_caption(screen, "FREE CELLS", layout.column_left(0),
                                    layout.column_left(3) + cw, top_y - 3, cw)
                self._group_caption(screen, "FOUNDATIONS", layout.column_left(4),
                                    layout.column_left(7) + cw, top_y - 3, cw)
                for i in range(4):
                    r = pygame.Rect(layout.column_left(i), top_y, cw, ch)
                    self._card(screen, art, m.cells[i], r, ("c", i, 0))
                for i in range(4):
                    r = pygame.Rect(layout.column_left(i + 4), top_y, cw, ch)
                    pile = m.foundations[i]
                    self._card(screen, art, pile[-1] if pile else None, r, ("f", i, 0))
            elif m.is_penguin:
                # All seven reserve cells and four foundation slots get real cards.
                top_slots = 11
                gap = max(4, min(cw // 6, (w - top_slots * cw) // 12))
                start_x = (w - (top_slots * cw + (top_slots - 1) * gap)) // 2
                self._group_caption(screen, "FLIPPER CELLS", start_x,
                                    start_x + 7 * cw + 6 * gap, top_y - 3, cw)
                self._group_caption(screen, "FOUNDATIONS",
                                    start_x + 7 * (cw + gap),
                                    start_x + 10 * (cw + gap) + cw,
                                    top_y - 3, cw)
                for i in range(7):
                    r = pygame.Rect(start_x + i * (cw + gap), top_y, cw, ch)
                    self._card(screen, art, m.cells[i], r, ("c", i, 0))
                for i in range(4):
                    r = pygame.Rect(start_x + (i + 7) * (cw + gap), top_y, cw, ch)
                    pile = m.foundations[i]
                    self._card(screen, art, pile[-1] if pile else None, r, ("f", i, 0))
            else:
                # Australian and Sir Tommy stock on left; waste/pending next;
                # foundations at right. This is the same pattern as Klondike.
                stock_x = max(10, layout.left)
                stock_r = pygame.Rect(stock_x, top_y, cw, ch)
                self._card(screen, art, None, stock_r, ("stock", 0, 0), back=bool(m.stock))
                if m.is_australian_redeal and not m.stock and m.redeals_remaining and m.waste:
                    self._slot_caption(screen, stock_r, "REDEAL")
                second_x = stock_x + layout.column_pitch
                r = pygame.Rect(second_x, top_y, cw, ch)
                if m.is_australian:
                    self._card(screen, art, m.waste[-1] if m.waste else None,
                               r, ("w", 0, 0))
                else:
                    self._card(screen, art, m.pending, r, ("p", 0, 0))
                foundation_gap = max(4, cw // 8)
                total = 4 * cw + 3 * foundation_gap
                start = max(second_x + cw + 8, w - total - max(10, cw // 3))
                for i in range(4):
                    rect = pygame.Rect(start + i * (cw + foundation_gap), top_y, cw, ch)
                    pile = m.foundations[i]
                    self._card(screen, art, pile[-1] if pile else None, rect, ("f", i, 0))
                    if m.is_tommy:
                        next_rank = len(pile) + 1
                        label = ("Needs " + RANK_HINT[next_rank]) if next_rank <= 13 else "COMPLETE"
                        font = pygame.font.Font(None, max(14, min(25, cw // 6)))
                        marker = font.render(label, True, COLOR_TEXT)
                        screen.blit(marker, marker.get_rect(centerx=rect.centerx,
                                                            bottom=rect.top - 3))
            for i, pile in enumerate(m.tableau):
                self._column(screen, art, layout, pile, i, layout.column_left(i), tableau_y)
        # Brief status / guidance below the board; no controls overlap the cards.
        if m.is_grid and not m.is_won():
            count = len(m.grid_legal_moves())
            text = (m.message if m.message else
                    str(count) + " legal move" + ("" if count == 1 else "s") +
                    "  |  Green gaps can be filled  |  Tap a gap or drag a card")
            if m.is_addiction and not m.message:
                text += "  |  Reshuffles left: " + str(m.reshuffles)
            font = pygame.font.Font(None, max(14, min(26, h // 32)))
            surface = font.render(text, True, COLOR_TEXT)
            if surface.get_width() > w - 20:
                surface = pygame.transform.smoothscale(surface, (w - 20, surface.get_height()))
            # This strip sits between the toolbar and the grid: never
            # cover the bottom row of cards on a phone-sized screen.
            screen.blit(surface, surface.get_rect(center=(w // 2, CHROME_BAND - 18)))
        if m.message and not m.is_won() and not m.is_grid:
            font = pygame.font.Font(None, max(19, min(30, h // 28)))
            img = font.render(m.message[:90], True, COLOR_TEXT)
            r = img.get_rect(center=(w // 2, min(h - 22, layout.tableau_top - 13 if not m.is_grid else h - 24)))
            shade = pygame.Surface((r.width + 25, r.height + 8), pygame.SRCALPHA)
            shade.fill((8, 48, 34, 220))
            screen.blit(shade, (r.x - 12, r.y - 4))
            screen.blit(img, r)
        if self.dragging and self.press_ref is not None and self.pointer_xy is not None:
            cards = self.model._source(self.press_ref)
            if cards:
                x = self.pointer_xy[0] - cw // 2
                y = self.pointer_xy[1] - ch // 4
                step = max(5, min(cw // 3, (h - y - ch) // max(1, len(cards))))
                for i, card in enumerate(cards):
                    screen.blit(art.of(card), (x, y + i * step))

    def hit(self, point):
        for rect, ref in reversed(self.regions):
            if rect.collidepoint(point):
                return ref
        return None

    def press(self, point):
        self.press_ref = self.hit(point)
        self.press_xy = point
        self.pointer_xy = point
        self.dragging = False

    def motion(self, point, slop=10):
        if self.press_ref is None or self.press_xy is None:
            return False
        self.pointer_xy = point
        if self.model._source(self.press_ref) and max(abs(point[0] - self.press_xy[0]),
                                                    abs(point[1] - self.press_xy[1])) > slop:
            self.dragging = True
        return self.dragging

    def release(self, point):
        source = self.press_ref
        self.press_ref = self.press_xy = self.pointer_xy = None
        target = self.hit(point)
        if source is None:
            self.selected = None
            self.dragging = False
            return None
        m = self.model
        if source[0] == "stock":
            self.dragging = False
            self.selected = None
            return "draw" if m.draw() else None
        if self.dragging:
            self.dragging = False
            self.selected = None
            if target and m.move(source, target):
                return "move"
            m.message = "That move is not allowed"
            return None
        self.dragging = False
        if m.is_grid:
            # A gap can itself be tapped. If only one card fits, move it now.
            # With multiple candidates, highlight them and let the player choose.
            if target is None or target[0] != "g":
                self.selected = None
                return None
            pos = target[1]
            legal = m.grid_legal_moves()
            if self.selected is not None and self.selected[0] == "g":
                previous = self.selected[1]
                if m.grid[previous] is None and (pos, previous) in legal:
                    self.selected = None
                    return "move" if m.move(("g", pos, 0), ("g", previous, 0)) else None
                if m.grid[pos] is None and (previous, pos) in legal:
                    self.selected = None
                    return "move" if m.move(("g", previous, 0), ("g", pos, 0)) else None
            if m.grid[pos] is None:
                possibilities = [src for src, dst in legal if dst == pos]
                if len(possibilities) == 1:
                    self.selected = None
                    return ("move" if m.move(("g", possibilities[0], 0),
                                              ("g", pos, 0)) else None)
                self.selected = target if possibilities else None
                m.message = ("Choose one of the highlighted cards" if possibilities
                             else "This gap is blocked")
            else:
                destinations = [dst for src, dst in legal if src == pos]
                if self.selected == target and len(destinations) == 1:
                    self.selected = None
                    return ("move" if m.move(target, ("g", destinations[0], 0))
                            else None)
                self.selected = target if destinations else None
                m.message = ("Tap a highlighted gap" if destinations else
                             "This card has no legal gap")
            return None
        if self.selected is not None and target is not None and target != self.selected:
            if m.move(self.selected, target):
                self.selected = None
                return "move"
        # Second tap on a selected card sends it home when possible.
        if source == self.selected and m.movable(source):
            self.selected = None
            return "move" if m.move_home(source) else None
        if m.movable(source):
            self.selected = source
            m.message = ""
        elif target and target[0] in ("f", "c", "t", "g"):
            # Keep selected card when tapping destination empty slot (handled above).
            pass
        else:
            self.selected = None
        return None

    def victory_launches(self):
        """Use the last rendered card positions for the classic cascading victory."""
        m = self.model
        coords = {ref: rect.topleft for rect, ref in self.regions}
        if m.is_grid:
            return [(card, coords.get(("g", i, 0), (0, 0)))
                    for i, card in enumerate(m.grid) if card is not None]
        result = []
        for suit, pile in enumerate(m.foundations):
            pos = coords.get(("f", suit, 0), (0, 0))
            result.extend((card, pos) for card in reversed(pile))
        return result
