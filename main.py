"""Pygbag browser entry with live iOS/Android viewport handling.

The original desktop/Juno entry in solitaire.py remains unchanged.
"""
import asyncio
import sys
import pygame

from game import SolitaireGame

FPS = 60
WEB = sys.platform == "emscripten"

if WEB:
    from platform import window


def viewport_size():
    """Return actual browser CSS pixels, never the stale portrait SDL default."""
    if not WEB:
        return (0, 0)  # Keep normal desktop full-screen behaviour.
    try:
        width = int(float(window.innerWidth))
        height = int(float(window.innerHeight))
        if width < 200 or height < 200:
            raise ValueError("Viewport not ready")
        # In portrait, prepare a landscape backing buffer behind the
        # rotate-phone overlay. When rotated, poll and resize to real size.
        return max(width, height), min(width, height)
    except (AttributeError, TypeError, ValueError):
        return (960, 540)


async def main():
    pygame.init()
    screen = pygame.display.set_mode(viewport_size())
    pygame.display.set_caption("Solitaire - 18 Games")
    clock = pygame.time.Clock()
    game = SolitaireGame(screen)
    game.draw()
    pygame.display.flip()

    running = True
    frames = 0
    while running:
        elapsed_ms = clock.tick(FPS)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break
            game.handle_event(event)
        if not running:
            break

        frames += 1
        resized = False
        # Pygbag does not reliably propagate VIDEORESIZE on mobile Safari.
        # Poll JS viewport instead and rebuild geometry after orientation
        # changes, browser chrome collapsing, and tablet split-screen resize.
        if WEB and frames % 12 == 0:
            target = viewport_size()
            actual = screen.get_size()
            if abs(target[0] - actual[0]) >= 3 or abs(target[1] - actual[1]) >= 3:
                screen = pygame.display.set_mode(target)
                game.resize_display(screen)
                resized = True
                clock.tick()  # Drop accumulated resize time, not game time.

        game.update(0 if resized else elapsed_ms)
        if resized or events or game.is_animating():
            game.draw()
            pygame.display.flip()
        await asyncio.sleep(0)
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
