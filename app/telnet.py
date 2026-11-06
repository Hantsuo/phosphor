"""
The telnet bridge.

The board started on a phone line; this is the closest thing left. Same session
object, same screen buffer, same database — just raw bytes over TCP instead of a
WebSocket.

    python -m app.telnet            # listens on 0.0.0.0:8023
"""

import asyncio
import logging
import os

from . import boards, db
from . import session as session_module

logger = logging.getLogger(__name__)

IAC = 0xFF
DO, DONT, WILL, WONT, SB, SE = 0xFD, 0xFE, 0xFB, 0xFC, 0xFA, 0xF0


def _negotiate() -> bytes:
    """Ask the client for character-at-a-time mode and no local echo."""
    return bytes([IAC, WILL, 0x01, IAC, WILL, 0x03])


def split_keys(data: bytes) -> list[str]:
    """
    Turn raw telnet bytes into the key strings the session already understands.

    Strips IAC negotiation and subnegotiation, folds CR LF / CR NUL into one
    Enter, and maps DEL/BS to backspace.
    """
    keys: list[str] = []
    index = 0
    length = len(data)
    while index < length:
        byte = data[index]
        if byte == IAC and index + 1 < length:
            command = data[index + 1]
            if command == IAC:
                keys.append("\xff")
                index += 2
                continue
            if command == SB:
                end = index + 2
                while end + 1 < length and not (data[end] == IAC and data[end + 1] == SE):
                    end += 1
                index = end + 2
                continue
            index += 3
            continue
        if byte == 0x0D:
            keys.append("\r")
            if index + 1 < length and data[index + 1] in (0x0A, 0x00):
                index += 2
                continue
            index += 1
            continue
        if byte == 0x0A:
            index += 1
            continue
        if byte in (0x08, 0x7F):
            keys.append("\x7f")
            index += 1
            continue
        if 32 <= byte <= 126:
            keys.append(chr(byte))
        index += 1
    return keys


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """One caller, one session, until they hang up."""
    peer = writer.get_extra_info("peername")
    conn = db.connect()
    boards.seed(conn)
    session = session_module.Session(fast=os.environ.get("PHOSPHOR_FAST") == "1")

    def send(text: str) -> None:
        writer.write(text.encode("utf-8", "replace"))

    try:
        writer.write(_negotiate())
        send(session._render_boot())
        await writer.drain()

        while True:
            data = await reader.read(1024)
            if not data:
                break
            if session.check_idle():
                send("\r\n\r\n*** CARRIER LOST ***\r\n")
                break
            for key in split_keys(data):
                frame = await session.handle_key(conn, key)
                if frame == "carrier lost":
                    send("\r\n\r\n*** CARRIER LOST ***\r\n")
                    await writer.drain()
                    return
                if frame:
                    send(frame)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError):
        pass
    except Exception:  # noqa: BLE001
        logger.exception("telnet session failed for %s", peer)
    finally:
        session.disconnect()
        conn.close()
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass


async def serve(host: str = "0.0.0.0", port: int = 8023) -> None:
    """Start the telnet listener."""
    server = await asyncio.start_server(handle, host, port)
    logger.info("telnet listening on %s:%s", host, port)
    async with server:
        await server.serve_forever()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(serve(port=int(os.environ.get("PHOSPHOR_TELNET_PORT", "8023"))))


if __name__ == "__main__":
    main()
