"""
LAST CALL — the door game.

Five rooms, one fuse, one phone, and a board that has been dark since 1999.
The whole game is a pure state machine so it can be tested without a terminal.

    state = new_state()
    state, lines = command(state, "north")
"""

from __future__ import annotations

from dataclasses import dataclass, field

START_ROOM = "lobby"

ROOMS = {
    "lobby": {
        "name": "THE LOBBY",
        "desc": [
            "chairs bolted to the floor. a reception desk.",
            "a phone sits in its cradle. the line is dead.",
        ],
        "exits": {"n": "server", "e": "noc"},
        "items": ["phone"],
    },
    "server": {
        "name": "SERVER ROOM",
        "desc": [
            "racks hum in the dark. one breaker slot is empty.",
            "a panel of switches, all of them down.",
        ],
        "exits": {"s": "lobby", "w": "cold"},
        "items": ["breaker"],
    },
    "cold": {
        "name": "COLD AISLE",
        "desc": [
            "your breath shows. a toolbox lies open on the floor.",
            "something small and ceramic glints inside it.",
        ],
        "exits": {"e": "server"},
        "items": ["fuse"],
    },
    "noc": {
        "name": "NETWORK OPS",
        "desc": [
            "empty monitors, one green cursor blinking on a dead terminal.",
            "a flashlight hangs from a hook by the door.",
        ],
        "exits": {"w": "lobby"},
        "items": ["flashlight"],
    },
}

HELP = [
    "COMMANDS: LOOK, N, S, E, W, TAKE <ITEM>, USE <ITEM>,",
    "INVENTORY, HELP, QUIT. THE DOOR CLOSES WHEN YOU QUIT.",
]

WIN_TEXT = [
    "you lift the handset and dial the board's own number.",
    "somewhere down the wire, a modem answers.",
    "",
    "THE LINE IS OPEN. THE BOARD IS AWAKE.",
]

LOSE_TEXT = [
    "the lights go out before you finish.",
    "the board stays dark. try again.",
]


@dataclass
class GameState:
    """Everything LAST CALL remembers between commands."""

    room: str = START_ROOM
    inventory: list[str] = field(default_factory=list)
    breaker_fixed: bool = False
    won: bool = False
    moves: int = 0


def new_state() -> GameState:
    """Start a fresh game at the lobby."""
    return GameState()


def _has(state: GameState, item: str) -> bool:
    return item in state.inventory


def look(state: GameState) -> list[str]:
    """Describe the current room and what is lying around."""
    room = ROOMS[state.room]
    lines = [room["name"], ""] + room["desc"] + [""]
    here = [item for item in room["items"] if item not in state.inventory]
    if here:
        lines.append("YOU CAN SEE: " + ", ".join(i.upper() for i in here))
    exits = " ".join(sorted(room["exits"]))
    lines.append("EXITS: " + exits.upper())
    return lines


def command(state: GameState, text: str) -> tuple[GameState, list[str], bool]:
    """
    Apply one command.

    Returns (state, lines, still_playing). `still_playing` is False when the
    player won, lost, or quit.
    """
    text = (text or "").strip().lower()
    state.moves += 1

    if not text:
        return state, [">"], True

    if text in ("quit", "q", "exit"):
        return state, ["you hang up.", ""] + LOSE_TEXT, False

    if text in ("help", "?"):
        return state, HELP, True

    if text in ("look", "l"):
        return state, look(state), True

    if text in ("inventory", "i"):
        if not state.inventory:
            return state, ["you are carrying nothing but the move counter."], True
        return state, ["YOU CARRY: " + ", ".join(i.upper() for i in state.inventory)], True

    directions = {"n": "n", "north": "n", "s": "s", "south": "s", "e": "e", "east": "e", "w": "w", "west": "w"}
    if text in directions:
        room = ROOMS[state.room]
        target = room["exits"].get(directions[text])
        if not target:
            return state, ["the wall does not move."], True
        state.room = target
        return state, look(state), True

    if text.startswith("take "):
        item = text[5:].strip()
        room = ROOMS[state.room]
        if item not in room["items"] or item in state.inventory:
            return state, [f"there is no {item} here."], True
        if item == "breaker":
            return state, ["the breaker is bolted to the wall."], True
        if item == "phone":
            return state, ["the phone stays on the desk. it is the point."], True
        state.inventory.append(item)
        return state, [f"taken: {item}."], True

    if text.startswith("use "):
        item = text[4:].strip()
        if item == "phone":
            if state.room != "lobby":
                return state, ["the phone is in the lobby."], True
            if not state.breaker_fixed:
                return state, ["dead line. the board needs power first."], True
            state.won = True
            return state, WIN_TEXT, False
        if not _has(state, item):
            return state, [f"you do not have a {item}."], True
        if item == "fuse":
            if state.room != "server":
                return state, ["the fuse needs a socket."], True
            state.breaker_fixed = True
            state.inventory.remove("fuse")
            return state, ["the fuse seats with a click. the panel wakes up.", "somewhere a phone starts to ring."], True
        if item == "flashlight":
            return state, ["the beam finds dust, and nothing else. yet."], True
        return state, [f"nothing happens with the {item}."], True

    return state, [f"unknown command: {text.upper()}. TRY HELP."], True
