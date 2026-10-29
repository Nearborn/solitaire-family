"""Pygbag browser entry with reliable mouse/touch input and viewport resize."""
import asyncio
import json
import sys
import pygame

from game import SolitaireGame

FPS = 60
WEB = sys.platform == "emscripten"
if WEB:
    from platform import window


def viewport_size():
    if not WEB:
        return (0, 0)
    try:
        width = int(float(window.innerWidth))
        height = int(float(window.innerHeight))
        if width < 200 or height < 200:
            raise ValueError("Browser viewport not initialized")
        return max(width, height), min(width, height)
    except (AttributeError, TypeError, ValueError):
        return (960, 540)


def browser_pointer_events(screen):
    """Translate normalized DOM pointer events into genuine pygame coordinates.

    This path does not depend on SDL's CSS-to-framebuffer mapping, which varies
    with Safari's browser chrome, pinch scale and devicePixelRatio.
    """
    if not WEB:
        return None
    try:
        if not bool(window.solitairePointerReady):
            return None  # Pygame native mouse event fallback
        raw = window.solitaireDrainInput()
        commands = json.loads(str(raw))
        width, height = screen.get_size()
        result = []
        mapping = {
            "down": pygame.MOUSEBUTTONDOWN,
            "move": pygame.MOUSEMOTION,
            "up": pygame.MOUSEBUTTONUP,
        }
        for command in commands:
            kind = command.get("type")
            if kind not in mapping:
                continue
            x = round(float(command["x"]) * width)
            y = round(float(command["y"]) * height)
            result.append(pygame.event.Event(mapping[kind], {
                "pos": (x, y),
                "button": 1,
                "buttons": (kind != "up", False, False),
                "rel": (0, 0),
            }))
        return result
    except (AttributeError, ValueError, TypeError, KeyError) as error:
        # Do not break game frames if JS interop is temporarily unavailable.
        print("Browser pointer bridge error:", error)
        return None


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
        native_events = pygame.event.get()
        bridged = browser_pointer_events(screen)
        # If JS captures pointers, ignore the duplicate/unreliable SDL mouse
        # events. Keep keyboard and window events working in all cases.
        if bridged is not None:
            native_events = [
                e for e in native_events
                if e.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION,
                                  pygame.MOUSEBUTTONUP, pygame.FINGERDOWN,
                                  pygame.FINGERMOTION, pygame.FINGERUP)
            ]
            events = native_events + bridged
        else:
            events = native_events

        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break
            game.handle_event(event)
        if not running:
            break

        frames += 1
        resized = False
        if WEB and frames % 12 == 0:
            target = viewport_size()
            actual = screen.get_size()
            if abs(target[0] - actual[0]) >= 3 or abs(target[1] - actual[1]) >= 3:
                screen = pygame.display.set_mode(target)
                game.resize_display(screen)
                resized = True
                clock.tick()
        game.update(0 if resized else elapsed_ms)
        if resized or events or game.is_animating():
            game.draw()
            pygame.display.flip()
        await asyncio.sleep(0)
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
