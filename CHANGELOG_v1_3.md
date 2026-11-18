# Solitaire v1.3 — release notes

**New:** Black Hole, Zodiac, Gargantua, Beetle, Birthday (four-digit target), Beleaguered Castle. 24 selectable games in the unchanged main interface.

**FreeCell:** Preserve detailed illegal-move diagnostics, including supermove-capacity limit. The screenshots show moves above the maximum capacity; the standard restriction is unchanged. Capacity now has a dedicated test and helper.

**Layout:** The original classic layout now provides separate pitch/offset for top-row stock/waste/foundations, preventing overlap in Gargantua.

**Rules:** Gargantua two stock passes (with pass accounting restored by undo); Beetle fully face-up 44/60 deal, standard automatic completion; all four distinctive rule sets are implemented as isolated reversible state machines in `game/novel_games.py`.

**Testing:** 31 Python logic tests passed on the release archive. Static geometry smoke tests performed for the new boards at 1694×895, 1024×768 and 800×450 using a minimal Pygame interface stand-in. Full interactive rendering could not be executed in this build environment because Pygame is not installed and package networking is unavailable. Juno/desktop validation is still recommended for touch gestures, sound and visual overlap.
