"""
Tests for LAST CALL, the door game. Pure state machine, no terminal.
"""

from app import game


def test_new_game_starts_in_the_lobby() -> None:
    state = game.new_state()
    assert state.room == "lobby"
    assert state.inventory == []
    assert not state.won


def test_look_lists_exits_and_items() -> None:
    lines = game.look(game.new_state())
    joined = "\n".join(lines)
    assert "THE LOBBY" in joined
    assert "EXITS: E N" in joined or "EXITS: N E" in joined


def test_winning_path() -> None:
    state = game.new_state()

    state, lines, playing = game.command(state, "n")
    assert playing and state.room == "server"

    state, lines, playing = game.command(state, "w")
    assert playing and state.room == "cold"

    state, lines, playing = game.command(state, "take fuse")
    assert "fuse" in state.inventory

    state, lines, playing = game.command(state, "e")
    state, lines, playing = game.command(state, "use fuse")
    assert state.breaker_fixed
    assert "fuse" not in state.inventory

    state, lines, playing = game.command(state, "s")
    assert state.room == "lobby"

    state, lines, playing = game.command(state, "use phone")
    assert state.won
    assert playing is False
    assert any("LINE IS OPEN" in line for line in lines)


def test_phone_needs_power() -> None:
    state = game.new_state()
    state, lines, playing = game.command(state, "use phone")
    assert playing is True
    assert not state.won
    assert any("dead line" in line for line in lines)


def test_fuse_needs_the_server_room() -> None:
    state = game.new_state()
    state, _, _ = game.command(state, "n")
    state, _, _ = game.command(state, "w")
    state, _, _ = game.command(state, "take fuse")
    state, lines, _ = game.command(state, "use fuse")
    assert not state.breaker_fixed
    assert any("needs a socket" in line for line in lines)


def test_walls_and_unknown_commands() -> None:
    state = game.new_state()
    state, lines, _ = game.command(state, "s")
    assert any("wall" in line for line in lines)

    state, lines, _ = game.command(state, "dance")
    assert any("UNKNOWN COMMAND" in line.upper() for line in lines)


def test_quit_ends_the_game() -> None:
    state = game.new_state()
    state, lines, playing = game.command(state, "quit")
    assert playing is False
    assert any("lights go out" in line for line in lines)
