"""The game, assembled — and the reason its loop sleeps between moves.

Patience is turn-based: for most of a game the picture on the screen is still correct, and `is_animating` is what tells `solitaire.py` it can block in `pygame.event.wait()`.
"""
import pygame

from .drag import Drag
from .layout import Layout
from .motion import (DEAL_MS, ROW_DEAL_MS, RUN_HOME_MS, Cascade, Flight,
                     Notice, SnapBack, TurnOver)
from .paint import Painter
from .rules import KLONDIKE, VARIANTS, SPECIAL_VARIANTS, SpecialVariant
from .extra_board import SpecialBoard, special_layout
from .more_games import MORE_GAMES
from .more_board import MoreBoard, more_layout
from .sheet import Art
from .sounds import Sounds
from .table import (STOCK, Flip, Table, Transfer, column, deal_from_stock,
                    foundation, move_to, recycle_waste, send_home,
                    stock_refused_by_an_empty_column)

DEALING = "dealing"
PLAYING = "playing"
CASCADE = "cascade"
WON = "won"


class SolitaireGame:
    """One table, one finger, eighteen rule sets to choose from and four states to be in."""

    variants = VARIANTS + SPECIAL_VARIANTS

    def __init__(self, screen):
        self.screen = screen
        self.layout = None
        self.art = None
        self.sounds = Sounds()
        self.table = Table(KLONDIKE)
        self.special = None
        self.special_won = False
        self.rules_open = False
        self.new_game()

    # -- starting over --

    def new_game(self, variant=None):
        """The art is re-cut only when the card comes out at a different size — the one part of this that costs anything."""
        variant = variant or self.current_variant
        self.rules_open = False
        if isinstance(variant, SpecialVariant):
            self.special = (MoreBoard(variant.name) if variant.name in MORE_GAMES
                            else SpecialBoard(variant.name))
            self.special_variant = variant
            self.special_won = False
            width, height = self.screen.get_size()
            previous_card_width = self.layout.card_width if self.layout is not None else None
            self.layout = (more_layout(width, height, variant)
                           if variant.name in MORE_GAMES
                           else special_layout(width, height, variant))
            if self.art is None or self.layout.card_width != previous_card_width:
                self.art = Art(self.layout.card_width, self.layout.card_height)
            self.painter = Painter(self.screen, self.layout, self.art)
            self.state = PLAYING
            self.deal = self.homing = self.snap_back = self.turning = None
            self.notice = self.cascade = None
            self.cascade_painted = False
            self.won_background = None
            self.pressed = None
            self.picker_open = False
            self.pressed_row = None
            self.sounds.shuffle.play()
            return
        self.special = None
        self.special_won = False
        width, height = self.screen.get_size()
        layout = Layout(width, height, variant)
        if self.art is None or layout.card_width != self.layout.card_width:
            self.art = Art(layout.card_width, layout.card_height)
        self.layout = layout
        self.painter = Painter(self.screen, layout, self.art)
        self.drag = Drag(layout)

        self.table.new_deal(variant=variant)
        self.state = DEALING
        self.deal = Flight(self._opening_flights(variant.deal.order), DEAL_MS)
        self.homing = None
        self.snap_back = None
        self.turning = None
        self.notice = None
        self.cascade = None
        self.cascade_painted = False
        self.won_background = None
        self.pressed = None
        self.picker_open = False
        self.pressed_row = None
        self.sounds.shuffle.play()

    @property
    def current_variant(self):
        return self.special_variant if self.special is not None else self.table.variant

    # -- the same toolbar/menu for both engines; the special board only adds piles --

    def _special_press(self, point):
        if self.rules_open:
            self.rules_open = False
            return
        if self.state == CASCADE:
            self._end_cascade()
            return
        if self.state == WON:
            self.new_game()
            return
        if self.picker_open:
            self.pressed_row = self.layout.picker_row_at(point, len(self.variants))
            return
        if (self.special.model.is_addiction and
                self.layout.reshuffle_button.collidepoint(point)):
            self.pressed = "reshuffle"
            return
        button = self.layout.button_at(point)
        if button is not None:
            self.pressed = button
            return
        self.special.press(point)

    def _special_release(self, point):
        if self.rules_open or self.state in (CASCADE, WON):
            return
        if self.picker_open:
            self._release_on_the_list(point)
            return
        button, self.pressed = self.pressed, None
        if button is not None:
            if button == "reshuffle":
                if self.layout.reshuffle_button.collidepoint(point):
                    if self.special.model.reshuffle():
                        self.special.selected = None
                        self.sounds.fan.play()
                return
            if button != self.layout.button_at(point):
                return
            if button == "undo":
                self._special_undo()
            elif button == "new":
                self.new_game()
            elif button == "rules":
                self.rules_open = True
            else:
                self.picker_open = True
            return
        result = self.special.release(point)
        if result == "draw":
            self.sounds.slide.play()
        elif result == "move":
            self.sounds.place.play()
        if result in ("move", "draw") and self.special.model.is_won():
            self._start_special_cascade()

    def _special_undo(self):
        if self.special.model.undo():
            self.special.selected = None
            self.special_won = False
            self.sounds.slide.play()

    # -- cards crossing the table --

    def _opening_flights(self, order):
        """Thrown from the stock's corner even in Yukon, which has no stock: that is where a dealer's hand is."""
        start = self.layout.pile_rect(STOCK).topleft
        placed = [0] * len(self.table.columns)
        flights = []
        for index in order:
            cards = self.table.columns[index]
            card_index = placed[index]
            placed[index] += 1
            flights.append(self._flight(cards, column(index), card_index, start))
        return flights

    def _row_flights(self, heights):
        """`heights` is how deep each column stood before the tap, so what flies is what the row actually left on the table."""
        start = self.layout.pile_rect(STOCK).topleft
        flights = []
        for number, cards in enumerate(self.table.columns):
            for index in range(heights[number], len(cards)):
                flights.append(self._flight(cards, column(number), index, start))
        return flights

    def _flight(self, cards, identifier, index, start):
        return (cards[index], identifier, start,
                self.layout.card_rect(identifier, index, cards).topleft)

    def _column_corners(self, into):
        """Called from inside `Table.do`, at the one moment a finished run is still lying in its column."""
        for index in range(len(self.table.columns)):
            cards = self.table.columns[index]
            left = self.layout.pile_rect(column(index)).left
            for card, top in zip(cards, self.layout.fan_offsets(cards)):
                into[id(card)] = (left, top)

    def _run_home_flights(self, tidying, corners):
        """`tidying` is what the table added of its own accord."""
        flights = []
        for move in tidying:
            if not isinstance(move, Transfer) or move.destination[0] != "foundation":
                continue
            home = self.layout.pile_rect(move.destination).topleft
            for card in self.table.pile(move.destination)[-move.count:]:
                flights.append((card, move.destination, corners[id(card)], home))
        return flights

    @property
    def shows_buttons(self):
        return self.state in (DEALING, PLAYING)

    def is_animating(self):
        """If nothing is moving, the loop can sleep until the table is touched."""
        if self.special is not None:
            return self.state == CASCADE
        return (self.deal is not None or self.homing is not None
                or self.snap_back is not None or self.turning is not None
                or self.notice is not None or self.state == CASCADE)

    # -- what a touch means --

    def handle_event(self, event):
        if self.special is not None:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._special_press(event.pos)
            elif event.type == pygame.MOUSEMOTION and not self.rules_open and self.state == PLAYING:
                self.special.motion(event.pos, max(9, self.layout.card_width // 10))
            elif event.type == pygame.MOUSEBUTTONUP:
                self._special_release(event.pos)
            elif event.type == pygame.KEYDOWN:
                if self.rules_open:
                    self.rules_open = False
                elif self.state == CASCADE:
                    self._end_cascade()
                elif self.state == WON:
                    self.new_game()
                elif event.key == pygame.K_n:
                    self.new_game()
                elif event.key == pygame.K_u or (event.key == pygame.K_z and event.mod & pygame.KMOD_META):
                    self._special_undo()
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._press(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            if self.drag.move(event.pos):
                self.sounds.slide.play()  # the moment a touch became a drag
        elif event.type == pygame.MOUSEBUTTONUP:
            self._release(event.pos)
        elif event.type == pygame.KEYDOWN:
            self._key(event)

    def _press(self, point):
        if self.rules_open:
            self.rules_open = False
            return
        if self.state == CASCADE:
            self._end_cascade()  # any touch stops the cards falling
            return
        if self.state == WON:
            self.new_game()
            return
        if self.deal is not None or self.homing is not None:
            # A touch while cards are in the air puts the rest of them down at once.
            self.deal = None
            self.homing = None
            self.state = PLAYING
            # A tap on the STOCK deals the next row rather than settling the one before it.
            landed_on = self.layout.card_at(self.table, point)
            if landed_on is None or landed_on[0] != STOCK:
                return
        if self.picker_open:
            self.pressed_row = self.layout.picker_row_at(point, len(self.variants))
            self.drag.break_tap()
            return

        button = self.layout.button_at(point)
        if button is not None:
            self.pressed = button
            self.drag.break_tap()  # a plate press is not the second half of anything
            return

        target = self.layout.card_at(self.table, point)
        if target is None:
            self.drag.break_tap()  # neither is a touch on bare felt
            return
        # Asked of every touch on a card: it is what clears the last tap.
        second_tap = self.drag.is_second_tap(target)
        if target[0] == STOCK:
            self._tap_stock()
        elif second_tap and target[1] == len(self.table.pile(target[0])) - 1:
            # Only the top card can go home, so a double-tap on a buried one picks its run up instead.
            self._commit(send_home(self.table, target[0]))
        else:
            self.snap_back = None  # a card still sliding back has arrived
            self.drag.start(self.table, target, point)

    def _release(self, point):
        if self.rules_open:
            return
        if self.picker_open:
            self._release_on_the_list(point)
            return
        button, self.pressed = self.pressed, None
        if button is not None:
            if button != self.layout.button_at(point):
                return  # the finger slid off the plate before letting go
            if button == "undo":
                self._undo()
            elif button == "new":
                self.new_game()
            elif button == "rules":
                self.rules_open = True
            else:
                self.picker_open = True
            return
        if not self.drag.holding:
            return

        # Where the finger let go need not be where the last motion event left the card: a flick can end somewhere the game never saw.
        self.drag.move(point)
        cards = self.drag.cards(self.table)
        held = self.drag.rect()
        source, index, count, moved, position, home = self.drag.release()
        if not moved:
            # A tap may be the first half of a double-tap, so it is remembered.
            self.drag.record_tap((source, index))
            return

        target = self.layout.drop_target(self.table, held)
        moves = move_to(self.table, source, count, target) if target is not None else None
        if moves is None:
            self.snap_back = SnapBack(cards, source, index, position, home)
            if target != source:
                self.sounds.shove.play()  # refused; a card put back where it came from is silent
        else:
            self._commit(moves)

    def _release_on_the_list(self, point):
        """Any touch closes the list; letting go on the row it started on picks it."""
        row, self.pressed_row = self.pressed_row, None
        self.picker_open = False
        if row is None or row != self.layout.picker_row_at(point, len(self.variants)):
            return
        variant = self.variants[row]
        # A hand cannot be carried into another rule set, so choosing one deals again.
        if variant is not self.current_variant:
            self.new_game(variant)

    def _tap_stock(self):
        moves = deal_from_stock(self.table)
        if moves is not None:
            heights = [len(cards) for cards in self.table.columns]
            action = self._carry_out(moves)
            self.sounds.slide.play()
            if self.homing is not None:
                self.sounds.place.play()  # a row of ten can finish a run
            # The move is already made; the flight is only so the player can see where the ten came from.
            flights = self._row_flights(heights)
            if flights:
                self.deal = Flight(flights, ROW_DEAL_MS)
            self._settle(action)
            return
        moves = recycle_waste(self.table)
        if moves is not None:
            self.notice = None
            self.table.do(moves)
            self.sounds.fan.play()
            return
        # Refusing to deal onto an empty column is a rule, so it is refused out loud and on the table; a spent stock says nothing.
        if stock_refused_by_an_empty_column(self.table):
            self.sounds.shove.play()
            self.notice = Notice()

    def _key(self, event):
        if self.rules_open:
            self.rules_open = False
        elif self.state == CASCADE:
            self._end_cascade()
        elif self.state == WON:
            self.new_game()
        elif event.key == pygame.K_n:
            self.new_game()
        elif event.key == pygame.K_u or (
                event.key == pygame.K_z
                and event.mod & (pygame.KMOD_META | pygame.KMOD_CTRL)
                and not event.mod & pygame.KMOD_SHIFT):
            # Shift+Cmd+Z is Redo, and there is no redo here. Undo also waits while a finger holds a run: it would change the table under the cards in hand.
            if not self.drag.holding:
                self._undo()

    # -- carrying a move out --

    def _commit(self, moves):
        if moves is None:
            return
        action = self._carry_out(moves)
        self.sounds.place.play()
        self._settle(action)

    def _carry_out(self, moves):
        """Answers what the table did, which is not always the moves that were asked for."""
        corners = {}
        action = self.table.do(
            moves, before_tidying=lambda: self._column_corners(corners))
        going_home = self._run_home_flights(action[len(moves):], corners)
        self.homing = Flight(going_home, RUN_HOME_MS) if going_home else None
        return action

    def _settle(self, action):
        self.notice = None
        for move in action:
            if isinstance(move, Flip):
                self.turning = TurnOver(move.pile, len(self.table.pile(move.pile)) - 1)
                self.sounds.slide.play()
        if self.table.is_won():
            self._start_cascade()

    def _undo(self):
        if self.state != PLAYING or not self.table.undo():
            return
        self.turning = None
        self.snap_back = None
        self.deal = None  # a row taken back is not still on its way out
        self.homing = None
        self.sounds.slide.play()

    # -- winning --

    def _start_special_cascade(self):
        """Use the original bouncing-card animation for all added games."""
        self.state = CASCADE
        self.special_won = True
        self.cascade_painted = False
        self.sounds.win.play()
        launches = self.special.victory_launches()
        width, height = self.screen.get_size()
        self.cascade = Cascade(launches, width, height,
                               self.layout.card_width, self.layout.card_height)

    def _start_cascade(self):
        self.state = CASCADE
        self.turning = None
        self.snap_back = None
        self.notice = None
        # The run that wins a Spider is still in the air here, and the table is painted once from now on.
        self.homing = None
        self.cascade_painted = False
        self.sounds.win.play()

        remaining = [list(pile) for pile in self.table.foundations]
        launches = []
        while any(remaining):
            for index, pile in enumerate(remaining):
                if pile:
                    corner = self.layout.pile_rect(foundation(index)).topleft
                    launches.append((pile.pop(), corner))
        width, height = self.screen.get_size()
        self.cascade = Cascade(launches, width, height,
                               self.layout.card_width, self.layout.card_height)

    def _end_cascade(self):
        self.state = WON
        self.cascade = None
        self.won_background = None  # the next draw keeps what the cards left behind

    # -- the frame --

    def update(self, elapsed_ms):
        if self.special is not None:
            if self.cascade is not None:
                self.cascade.update(elapsed_ms)
                if self.cascade.finished:
                    self._end_cascade()
            return
        if self.deal is not None:
            self.deal.update(elapsed_ms)
            if self.deal.finished:
                self.deal = None
        if self.deal is None and self.state == DEALING:
            self.state = PLAYING
        if self.homing is not None:
            self.homing.update(elapsed_ms)
            if self.homing.finished:
                self.homing = None
        if self.snap_back is not None:
            self.snap_back.update(elapsed_ms)
            if self.snap_back.finished:
                self.snap_back = None
        if self.turning is not None:
            self.turning.update(elapsed_ms)
            if self.turning.finished:
                self.turning = None
        if self.notice is not None:
            self.notice.update(elapsed_ms)
            if self.notice.finished:
                self.notice = None
        if self.cascade is not None:
            self.cascade.update(elapsed_ms)
            if self.cascade.finished:
                self._end_cascade()

    def draw(self):
        if self.special is not None:
            if self.state == CASCADE:
                if not self.cascade_painted:
                    self.painter.draw_table(self)
                    self.cascade_painted = True
                self.painter.draw_cascade(self.cascade)
            elif self.state == WON:
                if self.won_background is None:
                    self.won_background = self.screen.copy()
                self.painter.draw_won(self.won_background, title="Solved!")
            else:
                self.painter.draw_table(self)
            return
        if self.state == CASCADE:
            if not self.cascade_painted:
                # Painted once and never again: the falling cards are the only thing drawn now.
                self.painter.draw_table(self)
                self.cascade_painted = True
            self.painter.draw_cascade(self.cascade)
        elif self.state == WON:
            if self.won_background is None:
                self.won_background = self.screen.copy()
            self.painter.draw_won(self.won_background)
        else:
            self.painter.draw_table(self)
