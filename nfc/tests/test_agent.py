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