> **Android and iPhone web edition:** [Play Solitaire Collection](https://nearborn.github.io/solitaire-family/) — free, ad-free and installable from your browser. On a phone, turn the device **landscape**. On Android Chrome choose *Install app* / *Add to Home screen*; on iPhone Safari use *Share → Add to Home Screen*. No Python environment is required.\n>\n> **Mobile layout update (29 October 2026):** Browser viewport-aware canvas scaling, rotation without losing the current game, and refreshed offline caching. Device compatibility is still being verified.\n>\n> **Desktop / Juno:** Continue to run `solitaire.py`. The web entry point is `main.py`; GitHub Pages builds with Pygbag automatically.\n\n---\n\n# Solitaire — eighteen games

`solitaire.py` is an eighteen-game patience collection. Open it in Juno and press Run. Version 1.2 adds six more variants, a properly positioned Shuffle control in Addiction, and a two-column game chooser that retains the original UI style.

There is no clock, no score and nothing chasing you: every move can be taken back, and the game waits for as long as you like between them.

It does not fit in one file. `solitaire.py` is the way in and the file to Run; the game itself is the `game` folder beside it — `cards.py`, `rules.py`, `table.py`, `layout.py`, `sheet.py`, `sounds.py`, `motion.py`, `drag.py`, `paint.py` and `play.py`, which is the object all of them are assembled into. `assets` holds one card sheet and twelve recordings.

## The original six games

The plate in the top bar names the one you are playing, and the list drops out of it when you tap it. The three Spiders share a name, so the plate shows a coloured dot for each suit it is dealt from instead: one black, a black and a red, or two of each. A hand cannot be carried across into another set of rules, so choosing deals a fresh one.

- **Klondike** — seven columns, a face-down stock you turn over one card at a time, and columns built downwards in alternating colours. The one everybody knows, and the gentlest of the six.
- **Klondike Draw Three** — the same game, except the stock turns over three cards at once and only the top of the three is playable. A good deal harder.
- **Yukon** — no stock at all: all fifty-two are dealt out at the start, six of the seven columns wearing five face-up cards over a staircase of face-down ones. Columns still go down in alternating colours, but **any face-up card can be moved with everything sitting on top of it**, in whatever order that happens to be.
- **Spider (One Suit)** — the other solitaire people recognise, and the one to try first. Two decks, ten columns, eight foundations. Columns are built downwards in **any** suit, so almost anything will go anywhere; what you are working towards is a run from King down to Ace **all of one suit**, which leaves the table in one go. With every card a spade, every run you build is one suit already.
- **Spider (Two Suits)** — the same game in spades and hearts. A column still takes any card one rank lower, but only the single-suit stretch at the end of it can be carried away, so untangling one suit from the other is the whole game.
- **Spider (Four Suits)** — all four suits, two of each card. The hardest game on this table by a distance.


## Six variants introduced in v1.1

All eighteen choices now appear in the **same original dropdown** (two-column selector for comfortable touch targets). The original six
game definitions and their `Table`/`Transfer` move rules are unchanged. The six
additional boards use `game/extra_games.py` for their new pile/gap rules and
`game/extra_board.py` for layout and touch targeting. **Every game uses the same
OpenDecks card sheet, shared button renderer, background and menu.** There is
no secondary '+GAMES' launcher or new graphics style.

- **FreeCell** — eight tableau columns, four single-card free cells, and four
  ascending suit foundations. Build descending, alternating-colour runs; an
  empty column takes any card. Multi-card moves must fit the available free
  cells and empty columns (supermove capacity).
- **Penguin** — seven columns of seven cards, seven reserve cells (flipper),
  and four suit foundations. The first card dealt is the *beak*; the other
  three of its rank begin the foundations. Build down in suit with rank
  wraparound. Empty columns take only a card one rank below the beak (or
  a correctly ordered sequence starting with it). Suit sequences can move
  regardless of how many reserve cells are empty.
- **Australian Patience** — seven columns of four face-up cards, with a
  one-card stock and waste. Build down in suit; any card can carry all the
  cards above it in its column (even unsorted cards). Only Kings begin empty
  columns. Foundations build from Ace to King in suit. There is no redeal.
- **Old Patience / Sir Tommy** — draw one card from the stock, then place it
  onto one of **eight** waste piles or directly onto an eligible foundation.
  Cards once placed in a waste pile can move only from its top to a
  foundation. The four foundations build from Ace to King **regardless of
  suit**. This follows the eight-waste-pile version on Wikipedia; some other
  published Old Patience rules use four waste piles. No redeal.
- **Addiction Solitaire** — four rows of thirteen slots. Aces are removed
  to leave four gaps. Fill the first slot of a row with a Two, and later
  gaps with the next higher card of the same suit as the card to the left.
  A gap to the right of a King is blocked. Use up to three reshuffles of
  unfixed cards when there are no legal moves.
- **Maze Solitaire** — six rows of nine positions, with two extra blank
  positions and four Kings removed. Rows connect end-to-start, including
  the last position wrapping to the first. Fill a gap using an adjacent
  card of the same suit in ascending or descending sequence. The special
  Queen-to-Ace join may cross suits. Arrange four Ace-to-Queen suit runs
  with the first card an Ace and the last a Queen.

### Touch controls for the six additions

Drag a card (or legal sequence) onto its destination, exactly as with the
original games. Alternatively, **tap a card, then tap its destination**; this
helps with small grid gaps. Tap a selected card again to attempt to send it
to its foundation. The top-bar **Undo**, **New**, and **game selection** controls
are the originals, with the original large hit regions, plus a new **Rules** button displaying four short
points for the current game. Tap the stock to turn a card where applicable.
Undo reverses a whole logical move.

**Addiction and Maze** now indicate every possible starting card with a green
outline. A green gap has a legal move, and the number in it is the count of
cards that can fill it. A grey X means that gap is blocked. Tap any gap with
one matching card to move it immediately; if several cards match, the game
highlights all choices for you to tap. Alternatively, tap the card first and
tap a highlighted gap (or drag it there). Tap the selected card again when
it has only one destination to move it automatically. When Addiction has no
legal moves, the **Shuffle** button beside **Rules** in the top toolbar becomes enabled, for up
to three reshuffles. It remains disabled while a legal move is available.

**Free cells, flipper cells, foundations, empty tableau columns and waste
slots** now have subtle labels. In Sir Tommy each foundation also says
**Needs A**, **Needs 2**, ... **Needs K** to show which rank is legal next.
Sir Tommy's foundations are deliberately NOT suit-specific.

**Wins** in any of these additional games use the same classic
bouncing-card cascade and "tap again to deal" screen as the originals.

The complete project includes `game/__init__.py`, the original sprite and
sounds in `assets/`, and all original engine modules. Copy the entire
project if installing from scratch; no old project is required.

## Version 1.2: Six more variants (18 games total)

The **six original games and all six v1.1 additions are preserved**. The four
new nonstandard games are implemented in `game/more_games.py` (isolated move
rules) and `game/more_board.py` (touch targets and original sprite artwork).
Only the Australian redeal variant and Eight Off reuse the existing extended
move engine through guarded, game-specific rules.

These selections deliberately span casual, intermediate and demanding play.
Winning frequency varies substantially with the random deal and player choices;
the difficulty labels are relative, not measured win-rate guarantees.

| Game | Suggested challenge | What makes it distinct |
|---|---|---|
| **Australian Patience (One Redeal)** | Intermediate | Standard Australian Patience with **one** extra pass through the waste. Tap empty stock once to recycle remaining waste. The existing Australian game still has no redeals. |
| **Eight Off** | Easy–intermediate | Eight reserve cells (four occupied initially), eight six-card columns. Build descending in **suit**, empty columns Kings only. An approachable cousin of FreeCell. |
| **Golf** | Easy–intermediate | Seven columns of five cards. Clear the tableau by tapping exposed cards one rank above or below the discard, ignoring suit. Strict rules: no wrapping and **nothing can be played onto a King**. Tap the 16-card stock when stuck. |
| **TriPeaks** | Easy–intermediate | Clear three overlapping peaks by playing an exposed card one rank above/below the discard. Uncovering face-down cards creates new routes; tap stock to change rank. No A/K wrapping and no redeal. |
| **Relaxed Pyramid** | Intermediate | Remove exposed pairs totalling **13** (A+Q, 2+J, etc.). Kings clear individually. Match pyramid cards with one another or the waste top; draw one from stock. **One waste redeal is available**. Clear the **28-card pyramid** to win, even if stock/waste remains. |
| **Scorpion II** | Intermediate–demanding | Gentler variant of Scorpion: 49 cards in seven columns, with three face-down cards in each of the first **three** columns. Build down in suit; move any exposed card and all cards following it, even if unordered. Only Kings enter empty columns. Tap the three-card reserve to deal across the first three columns. Win by arranging four complete suited K-to-A columns. |

**Interaction:** Golf and TriPeaks use **single taps on exposed cards**. Pyramid
uses **tap card, tap its matching partner**, or tap a King once; tap stock to
reveal another waste card or, when empty, to use its one allowed redeal. Scorpion II and Eight Off support the familiar
**drag** or **tap source, tap destination** controls. Australian +1 plays like
Australian Patience with a one-time stock recycle. Undo, New, Rules and the
original cascading win animation remain available.

**Addiction Shuffle correction:** Its own fifth control is now placed **beside
Rules in the top toolbar**, within the same safe width as Undo, New, and game
selection. It is no longer behind the large top-left app control. It activates
only when no legal gap moves remain and reshuffles remain.

### Rule sources

All new selections follow the standard rules or explicitly named variants on
Wikipedia:
[Australian Patience](https://en.wikipedia.org/wiki/Australian_Patience),
[Eight Off](https://en.wikipedia.org/wiki/Eight_Off),
[Golf](https://en.wikipedia.org/wiki/Golf_(patience)),
[TriPeaks](https://en.wikipedia.org/wiki/Tri_Peaks_(game)),
[Pyramid (including Relaxed Pyramid)](https://en.wikipedia.org/wiki/Pyramid_(solitaire)),
and [Scorpion (including Scorpion II)](https://en.wikipedia.org/wiki/Scorpion_(solitaire)).

### Verification

The original v1.1 test suite is retained unchanged, with new tests in
`tests/test_new_variants.py`. Twenty-one deterministic model-level checks cover
card conservation, representative legal moves, undo, stock cycles, victory predicates,
and menu/rules registration. Run from the project root:

```bash
python -m unittest discover -s tests
```

The model, state/undo, card-count and rule tests can run without pygame; the
app itself requires pygame-ce as supported by Juno. Simulated drawing and
hit-target tests at landscape resolutions verified bounds and touch paths,
but this package still needs a final visual check on an actual iPhone/Juno.

## Playing

- **Drag a card** with one finger. It goes onto a column whose top card is one rank higher — the opposite colour in Klondike, Draw Three and Yukon, and any suit at all in the three Spiders, where a red nine sits happily on a black ten. An empty column takes a King and nothing else in the first three; in Spider it takes anything, which is why an empty column there is the most valuable thing on the table.
- **Pick a card up out of the middle** of a column and everything sitting on it comes too — if this game lets that stack travel. In Klondike and Draw Three it has to be a legally built run already; in Yukon any face-up card comes away with whatever is on it; in Spider it has to be a run all of **one suit**, which is the trade Spider makes for building so freely.
- A card with **nowhere to go** slides back where it came from and costs you nothing.
- **Tap the face-down pile** in the top left. In Klondike and Draw Three it turns the stock over onto the pile beside it, one card or three; tap it once it is empty and everything you turned over goes back underneath, as many times as you like. In Spider it deals a card face up to **every column at once** — five rows of ten, and that is the whole stock. Touch the table and the rest of a row arrives at once, or tap the pile again and the next row is already on its way. It will not deal while any column is empty: a card dropped into a gap fills in the one place you had to work with, so the game refuses and says why. Yukon has no such pile.
- **Double-tap a card** to send it home to its foundation, if that is where it can go: its Ace first, then that suit in order up to the King.
- **In Spider you never send anything home.** A foundation there takes one thing only — a finished King-to-Ace run of a single suit — and the instant you complete one, it lifts off the column by itself and flies away. That is the game rather than a convenience, and it is why a finished run is never left sitting where you could build on it again.
- **Undo** takes back the last thing you did, one step at a time, all the way to the deal. A whole row dealt across Spider's ten columns is one thing, and so is the card you played and the run it finished. There is no limit. **New** deals a fresh game of whatever you are playing.
- **Win** by getting every card home. The cards come off the foundations and paint the table on the way out. Tap to stop watching; tap again to deal another.
- With a **hardware keyboard**: `U` or `⌘Z` undoes, `N` deals a new game.
- This one is played entirely by touching the table, so it opens with **no on-screen controls** — a direction pad would cover the columns without ever being read. The button in the corner brings them back; nothing in the game listens for them.

## If you want to read it

**The rules are one file with no state in it**, `game/rules.py`, and all six games fit on a screen of it. Underneath they are the same game: columns built downwards, a stack lifted off one and carried somewhere else, and cards that go home when they are ready. They disagree about a handful of things — the deck, how a column is built, what may start an empty one, what may be lifted off one, what a foundation takes, and how the cards start out — so each of those is a small named function, and a rule set is one of each with a name on it:

```python
YUKON = Variant(
    name="Yukon", short_name="Yukon",
    builds_on=alternating_colours, lift=any_face_up_card,
    deal=OPEN_DEAL, stock=NO_STOCK)
```

Nothing in that file touches the table, moves anything, or knows that a move log exists — so a drag, a double-tap and anything you write against it yourself all ask the same questions of the same rule set. Yukon is Klondike with `a_built_run` swapped for `any_face_up_card` and no stock: two lines, and the whole game changes.

Spider is what the shape is worth when a game genuinely does not fit. Two decks over ten columns; it builds down in **any** suit while only letting a run of **one** suit be lifted; an empty column takes anything; and its foundations take one finished King-to-Ace run each rather than stacking cards up. Every one of those is a field on the same record, defaulted so a rule set only states what it changes. To add another classic-style game, write the rules it needs, make a `Variant` of them and add it to the list at the bottom of the file; the builders in `game/table.py` ask the table's own rule set every question they have, and `game/layout.py` measures the table for however many columns it turns out to want.

**Undo is the move log run backwards**, in `game/table.py`, and the whole of it is one line:

```python
def undo_of(moves):
    return [move.inverse() for move in reversed(moves)]
```

Nothing changes on the table except through a `Transfer` or a `Flip`, and each of them can say what its own opposite is. One thing you do is recorded as the little list of moves it took — dragging a card off a column is a transfer plus the flip of the card it uncovered, which is why taking it back is one undo and not two — and taking it back is that list, reversed, with every move replaced by its inverse. A list rather than a single move is also what lets a rule set do something big in one step: Spider's stock hands back ten transfers, one card to each column, and they land together and come back together. So there is no second code path that knows how to un-deal a card, and no copy of the table kept per move.

**The loop sleeps**, at the bottom of `solitaire.py`. Patience is turn-based: when nothing is moving, the picture on the screen is already right and stays right until somebody touches something. So the loop has two halves. While a card *is* moving — the deal turning out, a finished run on its way to a foundation, a refused card sliding back, the cards coming down at the end — it is clocked at sixty frames a second. The rest of the time it sits in `pygame.event.wait()`, which blocks: no frame is drawn and nothing is asked of the device until a finger or a key gives it something to answer. `game/play.py`'s `is_animating` chooses between the two.

**The cascade**, in `game/motion.py`, is an homage — everybody who has seen a game of solitaire won knows what happens next. Cards leave the foundations one at a time, each thrown sideways at a speed picked at random, falling under gravity and bouncing off the bottom of the canvas with a little less of itself left each time. What makes it look the way it does is one line that is missing: **the screen is never cleared**. Every card leaves a copy of itself everywhere it has been, so the table fills up with the arcs, and `game/paint.py` honours that by drawing nothing at all except the falling cards once the cascade has started.

**The table measures itself**, in `game/layout.py`. A row of columns wants width — seven of them, or Spider's ten — so on an iPhone held upright `solitaire.py` asks for the screen's two sides swapped and the window opens sideways. An iPad shows the table whichever way it is held. Either way the window cannot turn once it is open, and everything is worked out from the two numbers that arrive. The cards are drawn art rather than pixel art, so the cut blends each one down to whatever this table wants — which means a card can simply be the largest one where every column still fits across and the whole table still fits down, to the pixel. The gaps, the margins and the fan are then lengths in the card's own 42 × 60 box, scaled to whatever it came out at. How far one card is offset from the one below it is measured too: a face-up card shows 14 of its 60 rows, which is what the rank in the corner needs. A column with a long run in it will not fit at the full fan, so the two steps are squeezed together in proportion until it does, and drawing and hit-testing both ask the same function where a card is.

The rule set is an argument to that arithmetic rather than an exception inside it: it says how many columns to fit across, how many foundations the top row needs, and which face-down piles belong beside them. Klondike has a stock and a waste, Yukon neither, Spider a stock and no waste, and a pile a game has not got is left out rather than drawn as a slot a tap does nothing to.

## Credits

The cards are **OpenDecks**, a complete deck assembled out of older public-domain and CC0 drawings and released the same way: Creative Commons Zero. The court cards and the ornate ace of spades come from a public-domain vector deck; the pips, the rank letters and the back are three further CC0 drawings by other hands. `LICENSE.txt` beside this file names each of them and copies the deck's licence verbatim.

`assets/sprites.png` is the whole of the art: fifty-two faces and the card back at 252 × 360 each, laid out thirteen across and five down. The sheet carries no transparency — the only see-through part of a playing card is its four rounded corners, and the game carves those itself as it cuts each card to size. The empty slot is drawn rather than cut, and so are the coloured dots on the rule-set plate — a plate gives a mark about eighteen pixels, and a spade and a club are the same smudge at that size, so the plate carries the colours rather than the shapes.

The sound is twelve recordings, also in `assets`, all of them CC0: eleven from Kenney's **"Casino Audio"** — four takes of a card being set down, three of one card sliding over another, two of a card being shoved back, a deck being riffled and a deck being fanned — and one from Freesound, **"Horn.mp3" by rgeier2** (https://freesound.org/people/rgeier2/sounds/156879/), the horn that sounds when the last card goes home, and the same one Block Land sounds at its door. `LICENSE.txt` has both licences too.

The riffle is the one to know about: Klondike deals twenty-eight cards, Yukon fifty-two and Spider fifty-four, and every one of those deals takes the same three quarters of a second, because the riffle is one recording and it has to cover all of them.

Matched peaks are not matched loudness, which is what the numbers at the top of `game/sounds.py` are for: the slides are the sound the game makes most, so they sit at the bottom of the card set. The horn is the exception, and it is the file rather than the choice — it is a good deal quieter than the card sounds for the same peak, so it takes the highest number here to arrive at the same place: once a game, over a table that has gone quiet, and no louder than that.
