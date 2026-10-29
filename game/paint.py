"""Drawing the table. Every rectangle drawn in comes from `layout.py`, so what a card looks like and what a finger finds when it touches it cannot come apart."""
import pygame

from .cards import DIAMONDS, HEARTS, SUITS
from .quick_rules import QUICK_RULES

COLOR_TABLE = (30, 92, 68)
COLOR_BUTTON = (238, 242, 246)
COLOR_BUTTON_PRESSED = (196, 208, 218)
COLOR_BUTTON_SPENT = (86, 128, 106)  # nothing left to undo
COLOR_BUTTON_TEXT = (44, 54, 66)
COLOR_BUTTON_TEXT_SPENT = (140, 168, 152)
COLOR_TEXT = (246, 249, 250)
COLOR_TEXT_DIM = (176, 206, 190)
COLOR_PANEL = (12, 42, 30, 216)  # the winning screen, and the notice over the row
COLOR_BUTTON_ARROW = (128, 142, 156)  # the chevron that says a plate opens something

COLOR_PICKER_SHEET = (250, 251, 252)
COLOR_PICKER_HAIRLINE = (214, 222, 230)
COLOR_PICKER_CHOSEN = (223, 240, 231)  # the row in play
COLOR_PICKER_TICK = (24, 118, 84)
COLOR_PICKER_SHADOW = (6, 30, 20)

COLOR_DOT_BLACK = (28, 32, 38)
COLOR_DOT_RED = (176, 32, 44)

TITLE_FONT_FRACTION = 0.085  # of the canvas's short side
HINT_FONT_FRACTION = 0.038
MIN_FONT_PIXELS = 14
PANEL_PADDING_FRACTION = 0.05

PICKER_TICK_FRACTION = 0.42  # of a row's height
PICKER_TICK_WEIGHT_FRACTION = 11
PICKER_SHADOW_STEPS = 5
ARROW_FRACTION = 9  # of a plate's height: half the chevron's width
PLATE_DOT_FRACTION = 5  # of a plate's height: one colour dot

NOTICE_TEXT = "Fill every empty column before dealing another row"


class Painter:
    def __init__(self, screen, layout, art):
        self.screen = screen
        self.layout = layout
        self.art = art
        short_side = min(screen.get_size())
        self.title_font = _font(int(short_side * TITLE_FONT_FRACTION))
        self.hint_font = _font(int(short_side * HINT_FONT_FRACTION))
        self.button_font = _font(layout.button_font_height)
        # Drawn once rather than per frame: the plate is redrawn on every tick of an animation.
        dot = max(4, layout.variant_button.height // PLATE_DOT_FRACTION)
        self.dots = tuple(_dot(dot, COLOR_DOT_RED if suit in (HEARTS, DIAMONDS)
                               else COLOR_DOT_BLACK)
                          for suit in SUITS)

    # -- the table --

    def draw_table(self, game):
        self.screen.fill(COLOR_TABLE)
        if game.special is not None:
            game.special.draw(self.screen, self.art, self.layout)
            self._draw_buttons(game)
            self._draw_picker(game)
            self._draw_rules(game)
            return
        self._draw_row(game)
        self._draw_columns(game)
        self._draw_buttons(game)
        self._draw_moving_cards(game)
        self._draw_notice(game)
        self._draw_picker(game)
        self._draw_rules(game)

    def _draw_row(self, game):
        table = game.table
        for identifier in self.layout.row_piles:
            rect = self.layout.pile_rect(identifier)
            cards = table.pile(identifier)
            cards = cards[:_on_the_pile(game, identifier, len(cards))]
            self.screen.blit(self.art.of(cards[-1]) if cards else self.art.slot, rect)

    def _draw_columns(self, game):
        table = game.table
        turning = game.turning
        # Cards still in the air, and ones still waiting in the stock, are not on their columns yet.
        deal = game.deal
        for index in range(len(table.columns)):
            identifier = ("tableau", index)
            cards = table.columns[index]
            count = len(cards)
            if deal is not None:
                count = max(0, count - deal.waiting(identifier))
            count = _on_the_pile(game, identifier, count)
            if not count:
                self.screen.blit(self.art.slot, self.layout.pile_rect(identifier))
                continue
            mid_turn = turning.index if turning is not None and turning.pile == identifier else None
            offsets = self.layout.fan_offsets(cards)
            rect = self.layout.pile_rect(identifier)
            for card_index in range(count):
                rect.top = offsets[card_index]
                if card_index == mid_turn:
                    self._draw_turning(turning, cards[card_index], rect)
                else:
                    self.screen.blit(self.art.of(cards[card_index]), rect)

    def _draw_turning(self, turning, card, rect):
        art = self.art.of(card) if turning.shows_face else self.art.back
        width = max(1, round(rect.width * turning.width_fraction))
        squeezed = pygame.transform.scale(art, (width, rect.height))
        self.screen.blit(squeezed, (rect.centerx - width // 2, rect.top))

    def _draw_moving_cards(self, game):
        """Cards being dealt, going home, held, or put back."""
        for flight in (game.deal, game.homing):
            if flight is not None:
                for card, x, y in flight.in_flight:
                    self.screen.blit(self.art.of(card), (x, y))
        if game.snap_back is not None:
            self._draw_run(game.snap_back.cards, game.snap_back.position)
        if game.drag.holding:
            self._draw_run(game.drag.cards(game.table), game.drag.position)

    def _draw_run(self, cards, position):
        step = self.layout.fan_offsets(cards)
        rect = pygame.Rect(position, (self.layout.card_width, self.layout.card_height))
        for index, card in enumerate(cards):
            rect.top = position[1] + step[index] - step[0]
            self.screen.blit(self.art.of(card), rect)

    def _draw_buttons(self, game):
        if not game.shows_buttons:
            return
        can_undo = (bool(game.special.model.history) if game.special is not None
                    else game.table.can_undo())
        self._draw_button(self.layout.undo_button, "Undo",
                          enabled=can_undo, pressed=game.pressed == "undo")
        self._draw_button(self.layout.new_button, "New",
                          enabled=True, pressed=game.pressed == "new")
        variant = game.current_variant
        self._draw_button(self.layout.variant_button, variant.short_name,
                          enabled=True,
                          pressed=game.pressed == "variant" or game.picker_open,
                          suits=variant.suits if variant.shows_suits else (),
                          arrow=True)
        self._draw_button(self.layout.rules_button, "Rules", enabled=True,
                          pressed=game.pressed == "rules" or game.rules_open)
        if game.special is not None and game.special.model.is_addiction:
            m = game.special.model
            self._draw_button(self.layout.reshuffle_button,
                              "Shuffle " + str(m.reshuffles),
                              enabled=bool(m.reshuffles) and not m.has_grid_move(),
                              pressed=game.pressed == "reshuffle")

    def _draw_button(self, rect, label, enabled, pressed, suits=(), arrow=False):
        """Label, then a dot per suit, then `arrow`, laid out as one line and centred together."""
        if not enabled:
            plate, ink = COLOR_BUTTON_SPENT, COLOR_BUTTON_TEXT_SPENT
        elif pressed:
            plate, ink = COLOR_BUTTON_PRESSED, COLOR_BUTTON_TEXT
        else:
            plate, ink = COLOR_BUTTON, COLOR_BUTTON_TEXT
        pygame.draw.rect(self.screen, plate, rect, border_radius=rect.height // 3)

        font = (self.button_font if rect.height >= self.layout.undo_button.height
                else _font(max(13, rect.height // 2)))
        text = font.render(label, True, ink)
        # This also makes any unusually long translated label fit its plate.
        size = max(12, min(self.layout.button_font_height, rect.height // 2))
        while text.get_width() > rect.width - rect.height // 3 and size > 12:
            size -= 1
            text = _font(size).render(label, True, ink)
        gap = rect.height // 6
        dot_width = self.dots[0].get_width() if suits else 0
        dot_gap = max(1, dot_width // 6)
        dots_span = (len(suits) * dot_width + max(0, len(suits) - 1) * dot_gap) if suits else 0
        arrow_half = rect.height // ARROW_FRACTION if arrow else 0
        span = (text.get_width() + (gap + dots_span if suits else 0)
                + (gap + 2 * arrow_half if arrow else 0))

        left = rect.left + (rect.width - span) // 2
        self.screen.blit(text, text.get_rect(midleft=(left, rect.centery)))
        left += text.get_width()
        if suits:
            left += gap
            for suit in suits:
                dot = self.dots[suit]
                self.screen.blit(dot, dot.get_rect(center=(left + dot_width // 2,
                                                           rect.centery)))
                left += dot_width + dot_gap
            left -= dot_gap
        if arrow:
            left += gap + arrow_half
            self._draw_chevron((left, rect.centery), arrow_half, COLOR_BUTTON_ARROW)

    def _draw_chevron(self, centre, half, colour):
        x, y = centre
        drop = half * 2 // 5
        pygame.draw.lines(self.screen, colour, False,
                          [(x - half, y - drop), (x, y + drop), (x + half, y - drop)],
                          max(2, half // 3))

    def _draw_notice(self, game):
        """Laid over the row of piles: a message must not cover the columns it is asking the player to look at."""
        if game.notice is None:
            return
        fade = game.notice.fade
        text = self.hint_font.render(NOTICE_TEXT, True, COLOR_TEXT)
        text.set_alpha(round(255 * fade))
        line = text.get_height()
        panel = text.get_rect().inflate(2 * line, line)
        panel.center = (self.screen.get_rect().centerx,
                        self.layout.row_top + self.layout.card_height // 2)
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(shade, COLOR_PANEL[:3] + (round(COLOR_PANEL[3] * fade),),
                         shade.get_rect(), border_radius=panel.height // 3)
        self.screen.blit(shade, panel)
        self.screen.blit(text, text.get_rect(center=panel.center))

    def _draw_picker(self, game):
        if not game.picker_open:
            return
        count = len(game.variants)
        panel = self.layout.picker_panel(count)
        corner = self.layout.picker_corner
        inset = self.layout.picker_inset
        self._draw_sheet_shadow(panel, corner)
        pygame.draw.rect(self.screen, COLOR_PICKER_SHEET, panel, border_radius=corner)

        rows = self.layout.picker_rows(count)
        chosen = next((index for index, variant in enumerate(game.variants)
                       if variant is game.current_variant), None)
        for index, rect in enumerate(rows):
            marked = index == chosen
            if marked or game.pressed_row == index:
                pygame.draw.rect(self.screen,
                                 COLOR_PICKER_CHOSEN if marked else COLOR_BUTTON_PRESSED,
                                 rect, border_radius=corner)
            elif index and index - 1 != chosen:
                pygame.draw.line(self.screen, COLOR_PICKER_HAIRLINE,
                                 (rect.left + inset, rect.top),
                                 (rect.right - inset, rect.top))
            # Fit every entry inside its actual row, including on compact
            # landscape phones when twelve options are shown.
            label = game.variants[index].name
            font = self.button_font
            text = font.render(label, True, COLOR_BUTTON_TEXT)
            available = rect.width - inset * 2 - (rect.height if marked else 0)
            if text.get_width() > available or text.get_height() > rect.height * 9 // 10:
                font_size = min(self.layout.button_font_height,
                                max(10, rect.height * 8 // 10))
                font = _font(font_size)
                text = font.render(label, True, COLOR_BUTTON_TEXT)
                while text.get_width() > available and font_size > 10:
                    font_size -= 1
                    text = _font(font_size).render(label, True, COLOR_BUTTON_TEXT)
            self.screen.blit(text, text.get_rect(midleft=(rect.left + inset, rect.centery)))
            if marked:
                self._draw_tick(rect, inset)

    def _draw_rules(self, game):
        """A responsive four-point help sheet, shared by all twelve games."""
        if not game.rules_open:
            return
        width, height = self.screen.get_size()
        veil = pygame.Surface((width, height), pygame.SRCALPHA)
        veil.fill((5, 27, 22, 180))
        self.screen.blit(veil, (0, 0))

        name = game.current_variant.name
        bullets = QUICK_RULES.get(name, ())
        max_width = min(int(width * .88), max(410, int(height * 1.50)))
        panel = pygame.Rect(0, 0, max_width, 1)
        margin = max(16, min(32, height // 23))
        font_size = max(15, min(27, height // 24))
        # Keep the whole sheet on screen without shrinking the button bar.
        for size in range(font_size, 13, -1):
            font = _font(size)
            line_height = max(20, round(font.get_height() * 1.30))
            lines = []
            for bullet in bullets:
                words, current = bullet.split(), ""
                wrapped = []
                for word in words:
                    trial = (current + " " + word).strip()
                    if current and font.size(trial)[0] > max_width - 2 * margin - 18:
                        wrapped.append(current)
                        current = word
                    else:
                        current = trial
                if current:
                    wrapped.append(current)
                lines.append(wrapped)
            total_lines = sum(map(len, lines))
            target_height = margin * 3 + 55 + total_lines * line_height + len(bullets) * 8
            if target_height < height * .89 or size == 14:
                break
        panel.height = min(height - 14, target_height)
        panel.center = (width // 2, height // 2)
        self._draw_sheet_shadow(panel, max(12, margin // 2))
        pygame.draw.rect(self.screen, COLOR_PICKER_SHEET, panel,
                         border_radius=max(12, margin // 2))

        title_font = _font(max(size + 5, min(34, height // 19)))
        title = title_font.render(game.current_variant.short_name + " - Rules", True,
                                  COLOR_BUTTON_TEXT)
        self.screen.blit(title, (panel.left + margin, panel.top + margin))
        close = _font(max(14, size - 1)).render("Tap anywhere to close", True,
                                               COLOR_BUTTON_ARROW)
        self.screen.blit(close, (panel.right - margin - close.get_width(),
                                 panel.bottom - margin - close.get_height()))
        y = panel.top + margin + title.get_height() + 15
        for wrapped in lines:
            for n, line in enumerate(wrapped):
                prefix = "•  " if n == 0 else "   "
                # Use a dot shape rather than a font glyph on iOS/Juno.
                if n == 0:
                    pygame.draw.circle(self.screen, COLOR_PICKER_TICK,
                                       (panel.left + margin + 4, y + line_height // 2),
                                       max(3, size // 7))
                surface = font.render(line, True, COLOR_BUTTON_TEXT)
                self.screen.blit(surface, (panel.left + margin + 18, y))
                y += line_height
            y += 8

    def _draw_sheet_shadow(self, panel, corner):
        for step in range(PICKER_SHADOW_STEPS):
            spread = PICKER_SHADOW_STEPS - step
            shade = pygame.Surface((panel.width + 2 * spread, panel.height + 2 * spread),
                                   pygame.SRCALPHA)
            pygame.draw.rect(shade, COLOR_PICKER_SHADOW + (12,), shade.get_rect(),
                             border_radius=corner + spread)
            self.screen.blit(shade, (panel.left - spread, panel.top - spread + spread // 2))

    def _draw_tick(self, rect, inset):
        size = int(rect.height * PICKER_TICK_FRACTION)
        left = rect.right - inset - size
        top = rect.centery - size // 2
        pygame.draw.lines(self.screen, COLOR_PICKER_TICK, False,
                          [(left + size * 12 // 100, top + size * 55 // 100),
                           (left + size * 38 // 100, top + size * 81 // 100),
                           (left + size * 90 // 100, top + size * 19 // 100)],
                          max(2, rect.height // PICKER_TICK_WEIGHT_FRACTION))

    # -- the two screens that are not the table --

    def draw_cascade(self, cascade):
        """Where the falling cards have been since the last frame, and nothing else: what is already on the screen stays there."""
        for card, x, y in cascade.prints:
            self.screen.blit(self.art.of(card), (x, y))

    def draw_won(self, background, title="Every card home"):
        self.screen.blit(background, (0, 0))
        centre_x, centre_y = self.screen.get_rect().center
        headline = self.title_font.render(title, True, COLOR_TEXT)
        hint = self.hint_font.render("Tap anywhere to deal again", True, COLOR_TEXT_DIM)

        padding = int(min(self.screen.get_size()) * PANEL_PADDING_FRACTION)
        line = self.title_font.get_height()
        panel = pygame.Rect(0, 0,
                            max(headline.get_width(), hint.get_width()) + padding * 2,
                            line * 2 + padding * 2)
        panel.center = (centre_x, centre_y)
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(shade, COLOR_PANEL, shade.get_rect(), border_radius=padding)
        self.screen.blit(shade, panel)

        self.screen.blit(headline, headline.get_rect(
            center=(centre_x, panel.centery - line // 2)))
        self.screen.blit(hint, hint.get_rect(
            center=(centre_x, panel.centery + line // 2)))


def _on_the_pile(game, identifier, count):
    """How many of a pile's cards are actually sitting on it right now.

    A run under a finger, or in the air after a refusal, is still IN its pile and drawn elsewhere, so it is left off here. A run flying home is the other way round: the table has already put it on its foundation, so the foundation is drawn short until it arrives.
    """
    if game.drag.holding and game.drag.source == identifier:
        return min(count, game.drag.index)
    if game.snap_back is not None and game.snap_back.source == identifier:
        return min(count, game.snap_back.index)
    if game.homing is not None:
        count -= game.homing.waiting(identifier)
    return max(0, count)


def _font(size):
    return pygame.font.Font(None, max(MIN_FONT_PIXELS, size))


def _dot(size, colour):
    """A coloured disc, not a suit pip — at this size a spade and a club look the same. Drawn big and scaled down for a smooth edge."""
    scale = 4
    large = pygame.Surface((size * scale, size * scale), pygame.SRCALPHA)
    pygame.draw.circle(large, colour, (size * scale // 2, size * scale // 2), size * scale // 2)
    return pygame.transform.smoothscale(large, (size, size))
