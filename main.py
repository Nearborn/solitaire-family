"""Pygbag/Android-web entry. The original solitaire.py is not modified."""
import asyncio
import pygame
from game import SolitaireGame

FPS = 60


async def main():
    pygame.init()
    # Initialize in landscape: on Android, rotate the device before opening.
    screen = pygame.display.set_mode((0, 0))
    pygame.display.set_caption("Solitaire - 18 Games")
    clock = pygame.time.Clock()
    game = SolitaireGame(screen)
    game.draw()
    pygame.display.flip()

    running = True
    while running:
        # Do NOT use pygame.event.wait(): it would block the browser.
        elapsed_ms = clock.tick(FPS)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break
            game.handle_event(event)
        if not running:
            break
        game.update(elapsed_ms)
        if events or game.is_animating():
            game.draw()
            pygame.display.flip()
        await asyncio.sleep(0)  # Yield to pygame-web's cooperative browser loop.
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
