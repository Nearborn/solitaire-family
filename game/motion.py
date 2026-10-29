"""The four things that move, and the one that only says why nothing did. The table is already in its new state before any of them starts, so these only decide what the screen shows on the way there."""
import math
import random

MAX_FRAME_MS = 100  # a long pause must not teleport a falling card across the canvas

DEAL_CARD_MS = 26
KLONDIKE_DEAL_CARDS = 28
DEAL_MS = KLONDIKE_DEAL_CARDS * DEAL_CARD_MS  # every deal takes the same time, whatever it deals
ROW_DEAL_MS = 460  # Spider's row of ten
CARD_FLIGHT_MS = 190  # one card's own journey
RUN_HOME_MS = CARD_FLIGHT_MS  # a finished run crosses in one, because it crosses as one
SNAP_BACK_MS = 170
TURN_OVER_MS = 190
NOTICE_MS = 1800  # long enough to read the line before it goes
NOTICE_FADE_MS = 600

# The cascade, in fractions of the canvas, so it looks the same at every size.
CASCADE_MAX_SECONDS = 16.0
LAUNCH_INTERVAL_SECONDS = 0.16
LAUNCH_WINDOW_SECONDS = 8.5  # every card is thrown inside this
LAUNCH_SPEED_MIN = 0.30  # canvas widths per second, sideways
LAUNCH_SPEED_MAX = 0.65
LAUNCH_LIFT_MAX = 0.30  # canvas heights per second, upwards
CASCADE_GRAVITY = 2.0  # canvas heights per second per second
BOUNCE_DAMPING = 0.72  # what is left of the speed after a bounce
BOUNCE_FLOOR = 0.06
TRAIL_STEP_DIVISOR = 3  # a card prints itself at least every third of its own width
MAX_TRAIL_STEPS = 48


class Flight:
    """`flights` is one (card, pile, from, to) per card, in the order they leave."""

    def __init__(self, flights, total_ms):
        self.flights = list(flights)
        self.total_ms = float(total_ms)
        # Every card flies for the same length; the leftover span is what the launches spread across.
        self.flight_ms = max(1.0, min(CARD_FLIGHT_MS, self.total_ms))
        span = max(0.0, self.total_ms - self.flight_ms)
        beats = max(1, len(self.flights) - 1)
        self.card_ms = span / beats
        self.launch_ms = [span * index / beats for index in range(len(self.flights))]
        self.elapsed_ms = 0.0
        self.by_pile = {}
        for index, flight in enumerate(self.flights):
            self.by_pile.setdefault(flight[1], []).append(index)

    def update(self, elapsed_ms):
        self.elapsed_ms += min(elapsed_ms, MAX_FRAME_MS)

    @property
    def finished(self):
        return self.elapsed_ms >= self.total_ms

    def waiting(self, pile):
        return sum(1 for index in self.by_pile.get(pile, ())
                   if self.travelled(index) < 1.0)

    @property
    def in_flight(self):
        drawn = []
        for index, (card, _pile, start, home) in enumerate(self.flights):
            travelled = self.travelled(index)
            # Nought is a card AT its starting corner, not one still waiting, and it has to be drawn.
            if travelled < 0.0 or travelled >= 1.0:
                continue
            eased = 1.0 - (1.0 - travelled) ** 3  # away fast, easing into place
            drawn.append((card,
                          round(start[0] + (home[0] - start[0]) * eased),
                          round(start[1] + (home[1] - start[1]) * eased)))
        return drawn

    def travelled(self, index):
        """Below 0 while the card is still waiting its turn."""
        return min(1.0, (self.elapsed_ms - self.launch_ms[index]) / self.flight_ms)


class SnapBack:
    """It carries where the cards came from, so `paint.py` can leave that many off the pile — they never left the table."""

    def __init__(self, cards, source, index, start, home):
        self.cards = cards
        self.source = source
        self.index = index
        self.start = start
        self.home = home
        self.elapsed_ms = 0.0

    def update(self, elapsed_ms):
        self.elapsed_ms += min(elapsed_ms, MAX_FRAME_MS)

    @property
    def finished(self):
        return self.elapsed_ms >= SNAP_BACK_MS

    @property
    def position(self):
        fraction = min(1.0, self.elapsed_ms / SNAP_BACK_MS)
        eased = 1.0 - (1.0 - fraction) ** 3
        return (round(self.start[0] + (self.home[0] - self.start[0]) * eased),
                round(self.start[1] + (self.home[1] - self.start[1]) * eased))


class TurnOver:
    """Only the width moves, so a card turns on the spot without growing into the one below it."""

    def __init__(self, pile, index):
        self.pile = pile
        self.index = index
        self.elapsed_ms = 0.0

    def update(self, elapsed_ms):
        self.elapsed_ms += min(elapsed_ms, MAX_FRAME_MS)

    @property
    def finished(self):
        return self.elapsed_ms >= TURN_OVER_MS

    @property
    def fraction(self):
        return min(1.0, self.elapsed_ms / TURN_OVER_MS)

    @property
    def shows_face(self):
        """The swap happens edge-on, where nothing shows."""
        return self.fraction >= 0.5

    @property
    def width_fraction(self):
        return abs(1.0 - 2.0 * self.fraction)


class Notice:
    """A line of text that shows itself for a moment and then fades out."""

    def __init__(self):
        self.elapsed_ms = 0.0

    def update(self, elapsed_ms):
        self.elapsed_ms += min(elapsed_ms, MAX_FRAME_MS)

    @property
    def finished(self):
        return self.elapsed_ms >= NOTICE_MS

    @property
    def fade(self):
        """Full strength until the last stretch of its life."""
        return max(0.0, min(1.0, (NOTICE_MS - self.elapsed_ms) / NOTICE_FADE_MS))


class Cascade:
    """The screen is never cleared while this runs: every card leaves a copy of itself everywhere it has been, which is why `paint.py` draws nothing else."""

    def __init__(self, launches, width, height, card_width, card_height, rng=None):
        self.launches = list(launches)
        self.width = width
        self.height = height
        self.card_width = card_width
        self.card_height = card_height
        self.rng = rng or random
        # A longer deck shortens the beat, so the last card is still thrown in time to cross.
        self.launch_interval = min(LAUNCH_INTERVAL_SECONDS,
                                   LAUNCH_WINDOW_SECONDS / max(1, len(self.launches)))
        self.step = max(1, card_width // TRAIL_STEP_DIVISOR)
        self.elapsed_seconds = 0.0
        self.next_launch_seconds = 0.0
        self.flights = []  # (card, x, y, sideways speed, falling speed)
        self.prints = []  # where to draw them this frame, several per card

    @property
    def finished(self):
        return (self.elapsed_seconds >= CASCADE_MAX_SECONDS
                or (not self.flights and not self.launches))

    def update(self, elapsed_ms):
        seconds = min(elapsed_ms, MAX_FRAME_MS) / 1000.0
        self.elapsed_seconds += seconds
        self.prints = []
        if self.finished:
            return
        while self.launches and self.elapsed_seconds >= self.next_launch_seconds:
            self._launch()
            self.next_launch_seconds += self.launch_interval

        still_flying = []
        for flight in self.flights:
            flight = self._advance(flight, seconds)
            if -self.card_width < flight[1] <= self.width:
                still_flying.append(flight)
        self.flights = still_flying

    def _advance(self, flight, seconds):
        """Cut into short steps: a card can move further than its own width between frames, and a trail with gaps reads as a stutter."""
        card, x, y, speed_x, speed_y = flight
        distance = math.hypot(speed_x, speed_y) * seconds
        steps = max(1, min(MAX_TRAIL_STEPS, int(distance / self.step) + 1))
        slice_seconds = seconds / steps
        floor = self.height - self.card_height
        for _ in range(steps):
            speed_y += CASCADE_GRAVITY * self.height * slice_seconds
            x += speed_x * slice_seconds
            y += speed_y * slice_seconds
            if y > floor:
                y = floor
                speed_y = -speed_y * BOUNCE_DAMPING
                if abs(speed_y) < BOUNCE_FLOOR * self.height:
                    speed_y = 0.0  # spent: it slides off the side from here
            self.prints.append((card, round(x), round(y)))
        return (card, x, y, speed_x, speed_y)

    def _launch(self):
        card, position = self.launches.pop(0)
        speed = self.rng.uniform(LAUNCH_SPEED_MIN, LAUNCH_SPEED_MAX) * self.width
        # Away from whichever side it is nearer, so it crosses the table.
        towards = -1 if position[0] > self.width / 2 else 1
        lift = -self.rng.uniform(0.0, LAUNCH_LIFT_MAX) * self.height
        self.flights.append(
            (card, float(position[0]), float(position[1]), speed * towards, lift))
