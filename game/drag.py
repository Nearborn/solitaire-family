"""What a finger is doing between touching down and lifting off. The cards being dragged are still on their pile, so a refused drop is nothing at all — there is nothing to put back."""
import pygame

from .table import liftable

TAP_SLOP = 8  # how far a finger may wander and still be a tap, in the card's own box
DOUBLE_TAP_MS = 320


class Drag:
    def __init__(self, layout):
        self.layout = layout
        self.slop = layout.scaled(TAP_SLOP)
        self.source = None
        self.index = 0
        self.count = 0
        self.home = (0, 0)
        self.position = (0, 0)
        self.grab = (0, 0)  # the finger's offset inside the top card
        self.press_point = (0, 0)
        self.moved = False
        self.last_tap = None

    @property
    def holding(self):
        return self.source is not None

    def start(self, table, target, point):
        """Pick up what is under the finger, if any of it can be picked up."""
        source, index = target
        count = liftable(table, source, index)
        if not count:
            return False
        home = self.layout.card_rect(source, index, table.pile(source)).topleft
        self.source, self.index, self.count = source, index, count
        self.home = home
        self.position = home
        self.grab = (point[0] - home[0], point[1] - home[1])
        self.press_point = point
        self.moved = False
        return True

    def move(self, point):
        """True on the one move that turns a tap into a drag."""
        if not self.holding:
            return False
        became_a_drag = False
        if not self.moved:
            travel = max(abs(point[0] - self.press_point[0]),
                         abs(point[1] - self.press_point[1]))
            self.moved = travel > self.slop
            became_a_drag = self.moved
        self.position = (point[0] - self.grab[0], point[1] - self.grab[1])
        return became_a_drag

    def cards(self, table):
        return table.pile(self.source)[self.index:]

    def rect(self):
        """The top card's rectangle — what a drop target is judged against."""
        return pygame.Rect(self.position, (self.layout.card_width, self.layout.card_height))

    def release(self):
        state = (self.source, self.index, self.count, self.moved, self.position, self.home)
        self.source = None
        self.count = 0
        self.moved = False
        return state

    # -- taps --

    def is_second_tap(self, target):
        """The record is cleared either way, so three taps are one double and then a fresh start."""
        previous, when = self.last_tap or (None, 0)
        self.last_tap = None
        return (previous == target
                and pygame.time.get_ticks() - when <= DOUBLE_TAP_MS)

    def record_tap(self, target):
        self.last_tap = (target, pygame.time.get_ticks())

    def break_tap(self):
        """A touch anywhere else forgets the pending half of a double-tap."""
        self.last_tap = None
