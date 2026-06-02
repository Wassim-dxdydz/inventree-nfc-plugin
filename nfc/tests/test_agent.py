"""
Tests for the NFC agent Flask app.
All pyscard calls are mocked, so no USB reader required.
"""
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture()
def client():
    """
    Return a Flask test client with pyscard fully mocked
    """

    with patch("smartcard.CardMonitoring.CardMonitor"), \
    patch("smartcard.System.readers", return_value = [MagicMock()]):
        from agent.agent import app
        app.config["TESTING"]=True
        with app.test_client() as c: yield c

@pytest.fixture()
def client_no_reader():
    """
    Return a Flask test client with no reader plugged in.
    """

    with patch("smartcard.CardMonitoring.CardMonitor"), \
    patch("smartcard.System.readers", return_value = []):
        from agent.agent import app
        app.config["TESTING"]=True
        with app.test_client() as c: yield c

def test_health_reader_connected(client):
    with patch("agent.agent.readers", return_value = [MagicMock()]):
        res = client.get("/health")
    
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["reader_connected"] is True

def test_health_no_reader(client):
    with patch("agent.agent.readers", return_value = []):
        res = client.get("/health")
    
    assert res.status_code == 200
    data = res.get_json()
    assert data["reader_connected"] is False

def test_scan_once_returns_uid(client):
    """
    Agent unblocks immediately when a tag UID is pre-set in state.
    """

    with patch("agent.agent.readers", return_value = [MagicMock()]):
        import threading
        import agent.agent as ag

        def set_uid():
            import time
            time.sleep(0.05)
            ag._state.set("AABBCCDD")

        t = threading.Thread(target=set_uid, daemon=True)
        t.start()
        res = client.post("/scan/once", json={"timeout": 5})
        t.join()
        assert res.status_code == 200
        assert res.get_json()["uid"] == "AABBCCDD"

def test_scan_once_timeout(client):
    """
    Agent returns timeout error when no tag is scanned within the window.
    """

    with patch("agent.agent.readers", return_value = [MagicMock()]):
        import threading
        import agent.agent as ag

        def set_uid():
            import time
            time.sleep(0.05)
            ag._state.set("AABBCCDD")

        t = threading.Thread(target=set_uid, daemon=True)
        t.start()
        res = client.post("/scan/once")
        t.join()
        assert res.status_code == 408
        assert res.get_json()["error"] == "timeout"

def test_scan_once_no_reader(client):
    """
    Agent returns error 503 when no reader is plugged in.
    """

    with patch("agent.agent.readers", return_value = []):
        res = client.post("/scan/once", json={"timeout": 1})
        assert res.status_code == 503
        assert res.get_json()["error"] == "no_reader"

def test_scan_once_default_timeout(client):
    """
    Agent accepts missing timeout body and defaults to 30s.
    """

    with patch("agent.agent.readers", return_value = [MagicMock()]):
        from agent.agent import _state
        _state.set("AABBCCDD")
        res = client.post("/scan/once")
        assert res.status_code == 200
        assert res.get_json()["uid"] == "AABBCCDD"
