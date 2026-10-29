"""The twelve sound effects. Every failure answers with a silent stand-in rather than an exception."""
import os
import random

import pygame

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

# Levels chosen by ear; the numbers are 0 to 1.
SLIDE_VOLUME = 0.30  # the sound this game makes most
PLACE_VOLUME = 0.40
SHOVE_VOLUME = 0.45  # a refusal has to be heard
SHUFFLE_VOLUME = 0.38  # the riffle, under the deal
FAN_VOLUME = 0.30
WIN_VOLUME = 0.55

PLACE_COUNT = 4
SLIDE_COUNT = 3
SHOVE_COUNT = 2


class NoneSound:
    def play(self):
        pass


def load_sound(name, volume):
    if not pygame.mixer:
        return NoneSound()
    try:
        sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, name))
        sound.set_volume(volume)
        return sound
    except (pygame.error, OSError):
        return NoneSound()


class Variants:
    def __init__(self, pattern, count, volume):
        self.takes = [load_sound(pattern % number, volume)
                      for number in range(1, count + 1)]
        self.last = None

    def play(self):
        index = random.choice([i for i in range(len(self.takes)) if i != self.last])
        self.last = index
        self.takes[index].play()


class Sounds:
    def __init__(self):
        self.place = Variants("place%d.ogg", PLACE_COUNT, PLACE_VOLUME)
        self.slide = Variants("slide%d.ogg", SLIDE_COUNT, SLIDE_VOLUME)
        self.shove = Variants("shove%d.ogg", SHOVE_COUNT, SHOVE_VOLUME)
        self.shuffle = load_sound("shuffle.ogg", SHUFFLE_VOLUME)
        self.fan = load_sound("fan.ogg", FAN_VOLUME)
        self.win = load_sound("win.ogg", WIN_VOLUME)
