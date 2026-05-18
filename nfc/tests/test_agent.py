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
    assert data["reader_connected"] is True

def test_scan_once_returns_uid(client):
    """
    Agent unblocks immediately when a tag UID is pre-set in state.
    """

    with patch("agent.agent.readers", return_value = [MagicMock()]):
        from agent.agent import _state
        _state.set("AABBCCDD")
        res = client.post("/scan/once", json={"timeout": 5})
        assert res.status_code == 200
        assert res.get_json()["uid"] == "AABBCCDD"
