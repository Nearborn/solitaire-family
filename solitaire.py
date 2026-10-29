# Solitaire — six games of patience on one table, and the cards come down when you win
#
# Run THIS file. README.md has the rules and how to play.

import os
import sys

# Make the `game` folder beside this file importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from game import SolitaireGame

FPS = 60


def main():
    pygame.init()

    try:
        from juno import game as _juno_game
    except ImportError:  # not running inside Juno
        _juno_game = None
    if _juno_game is not None:
        _juno_game.controls("none")
        # The table wants width, and asking before the window opens is what opens it the wide way round.
        _juno_game.orientation("landscape")

    screen = pygame.display.set_mode((0, 0))
    pygame.display.set_caption("Solitaire")
    clock = pygame.time.Clock()
    game = SolitaireGame(screen)

    game.draw()
    pygame.display.flip()

    # Sixty a second while a card is moving, blocked in `event.wait()` while nothing is.
    running = True
    while running:
        if game.is_animating():
            elapsed_ms = clock.tick(FPS)
            events = pygame.event.get()
        else:
            events = [pygame.event.wait()] + pygame.event.get()
            clock.tick()  # discard the pause
            elapsed_ms = 0

        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break
            game.handle_event(event)
        if not running:
            break

        game.update(elapsed_ms)
        game.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
