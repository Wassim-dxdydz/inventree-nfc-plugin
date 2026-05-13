"""
NFC Agent — runs locally on the workstation with the USB reader.
Exposes 2 endpoints:
  GET  /health      → is the reader connected?
  POST /scan/once   → wait for a tag, return its UID
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

from flask import Flask, jsonify
from flask_cors import CORS
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.Exceptions import CardConnectionException, NoCardException
from smartcard.System import readers
from smartcard.util import toHexString

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("nfc-agent")

# The APDU command that tells an NFC tag: "give me your UID"
GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
SW_OK   = (0x90, 0x00)  # status word = success


# ── Thread-safe UID buffer ────────────────────────────────────────────────────
# When agent.py receives POST /scan/once, the HTTP request thread calls
# _state.take() which BLOCKS. Meanwhile, the PC/SC background thread
# (NFCObserver) detects the tag, reads the UID, and calls _state.set(uid)
# which UNBLOCKS the waiting HTTP thread. Clean, no polling.

@dataclass
class TagState:
    _lock:  threading.Lock  = field(default_factory=threading.Lock,  repr=False)
    _uid:   Optional[str]   = field(default=None,                    repr=False)
    _event: threading.Event = field(default_factory=threading.Event, repr=False)

    def set(self, uid: str) -> None:
        with self._lock:
            self._uid = uid
            self._event.set()

    def take(self, timeout: float = 15.0) -> Optional[str]:
        """Block until a tag arrives or timeout expires."""
        fired = self._event.wait(timeout=timeout)
        if not fired:
            return None
        with self._lock:
            uid = self._uid
            self._uid = None
            self._event.clear()
        return uid


_state = TagState()


# ── PC/SC card observer ───────────────────────────────────────────────────────
# pyscard's CardMonitor runs a background thread that calls update()
# every time a card is inserted or removed.

class NFCObserver(CardObserver):
    def update(self, observable, actions):
        added, _ = actions
        for card in added:
            uid = _read_uid(card)
            if uid:
                log.info("Tag scanned: %s", uid)
                _state.set(uid)


def _read_uid(card) -> Optional[str]:
    try:
        card.connection = card.createConnection()
        card.connection.connect()
        response, sw1, sw2 = card.connection.transmit(GET_UID)
        if (sw1, sw2) == SW_OK and response:
            return toHexString(response).replace(" ", "").upper()
        log.warning("Bad SW: %02X %02X", sw1, sw2)
        return None
    except (CardConnectionException, NoCardException) as e:
        log.warning("UID read failed: %s", e)
        return None
    finally:
        try:
            card.connection.disconnect()
        except Exception:
            pass


# ── Flask app ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
# Allow calls from InvenTree running in the browser (any localhost origin)
CORS(app, origins=["http://localhost:*", "http://127.0.0.1:*"])


@app.get("/health")
def health():
    return jsonify({"status": "ok", "reader_connected": bool(readers())}), 200


@app.post("/scan/once")
def scan_once():
    if not readers():
        # No USB reader plugged in
        return jsonify({"error": "no_reader"}), 503

    uid = _state.take(timeout=15.0)

    if uid is None:
        # User didn't scan anything within 15 seconds
        return jsonify({"error": "timeout"}), 408

    return jsonify({"uid": uid}), 200


# ── Start ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from waitress import serve
    monitor = CardMonitor()
    monitor.addObserver(NFCObserver())
    log.info("Agent ready on http://127.0.0.1:8765")
    serve(app, host="127.0.0.1", port=8765)