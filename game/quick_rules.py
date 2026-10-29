"""Four concise in-game rule reminders for each table.

Presentation only; no gameplay logic depends on these descriptions.
"""
QUICK_RULES = {
    "Klondike": (
        "Build tableau downward, alternating red and black.",
        "Move only face-up descending runs; empty columns take Kings.",
        "Tap the stock for one card; recycle the waste when empty.",
        "Build each suit from Ace through King on the foundations.",
    ),
    "Klondike Draw Three": (
        "Build tableau downward in alternating colours.",
        "Only Kings start an empty column.",
        "Stock flips three at a time; only the top waste card is playable.",
        "Build suit foundations from Ace to King.",
    ),
    "Yukon": (
        "All 52 cards are in seven columns; there is no stock.",
        "Build downward in alternating colours; Kings fill empty columns.",
        "Move any exposed card WITH every card below it, even if unordered.",
        "Build foundations upward by suit from Ace to King.",
    ),
    "Spider (One Suit)": (
        "Build down by rank; empty columns take any card.",
        "Only same-suit descending runs may move as a group.",
        "Tap stock for a card on every column (none may be empty).",
        "Complete King-to-Ace same-suit runs to clear them automatically.",
    ),
    "Spider (Two Suits)": (
        "Build down by rank, regardless of suit.",
        "Only same-suit descending runs may move as a group.",
        "Fill all empty columns before dealing ten more cards.",
        "Finish King-to-Ace single-suit runs to remove them.",
    ),
    "Spider (Four Suits)": (
        "Build down by rank; mixed suits may stack.",
        "Only same-suit descending runs may move together.",
        "Stock deals to all ten columns, only when none is empty.",
        "Remove eight complete King-to-Ace single-suit runs.",
    ),
    "FreeCell": (
        "Build down in alternating colours; any card fills an empty column.",
        "Four free cells each hold just one card.",
        "Move a whole run only if empty cells/columns can support it.",
        "Move all cards to Ace-to-King foundations by suit.",
    ),
    "Penguin": (
        "The beak is the first card; its three equals start foundations.",
        "Build tableau down IN SUIT, wrapping Ace to King.",
        "Only the rank immediately below the beak starts empty columns.",
        "Seven flipper cells hold one card each; build home from the beak.",
    ),
    "Australian Patience": (
        "Build tableau down by suit; only Kings fill empty columns.",
        "Move any exposed card plus every card below it, even unordered.",
        "Draw from stock one at a time; there is NO redeal.",
        "Build foundations up in suit from Ace through King.",
    ),
    "Old Patience / Sir Tommy": (
        "Draw one card; place it directly home or on any waste pile.",
        "Eight waste piles accept ANY card, but only their tops move home.",
        "Foundations build A, 2, 3 ... K, REGARDLESS OF SUIT.",
        "A buried waste card cannot be moved; no stock redeal.",
    ),
    "Addiction Solitaire": (
        "Four Aces are removed, creating four movable gaps.",
        "First column gaps take any 2; other gaps need the next in suit.",
        "Tap a highlighted gap/card or drag a card to its legal gap.",
        "Build four 2-to-K rows. Reshuffle blocked cards up to 3 times.",
    ),
    "Australian Patience (One Redeal)": (
        "Australian Patience's original tableau rules are unchanged.",
        "Build down by suit; empty columns accept only Kings.",
        "The stock turns one card at a time to the waste.",
        "When stock empties, tap it to recycle waste ONCE.",
    ),
    "Eight Off": (
        "Eight columns of six cards; four of eight reserve cells start occupied.",
        "Build tableau down in SUIT; empty columns accept Kings only.",
        "Each reserve cell holds one card; free cells enable group moves.",
        "Move all cards to same-suit Ace-to-King foundations.",
    ),
    "Golf": (
        "Clear seven five-card columns: only their bottom cards are exposed.",
        "Move a card one rank up or down onto the discard; suits ignored.",
        "No wrap (Ace/King); nothing may be placed onto a King.",
        "Tap stock for another discard card. No redeal; clear all 35.",
    ),
    "TriPeaks": (
        "Clear all three peaks by removing exposed, uncovered cards.",
        "Play cards one rank higher or lower than the discard, any suit.",
        "Stock draws one new discard; no redeal. A/K are not adjacent.",
        "Removing cards uncovers face-down cards higher in each peak.",
    ),
    "Relaxed Pyramid": (
        "Remove two uncovered cards totalling 13; Kings go alone.",
        "Pair exposed pyramid cards with each other or the waste top.",
        "Tap stock to turn up pairing cards; one waste redeal allowed.",
        "Clear all 28 pyramid cards to win (relaxed rules).",
    ),
    "Scorpion II": (
        "49 cards across seven columns; three hidden starters per left column.",
        "Build down in SUIT; move any face-up card with its tail.",
        "Empty columns take Kings; stock deals last three cards to left columns.",
        "Win with four full King-to-Ace columns in suit. No foundations.",
    ),
    "Maze Solitaire": (
        "Remove all Kings; six gaps remain in a continuous loop.",
        "Fill a gap with the next card in suit on its left OR prior on right.",
        "After a Queen, any Ace may follow; nothing goes before an Ace.",
        "Make four complete A-to-Q suit sequences around the grid.",
    ),
}
