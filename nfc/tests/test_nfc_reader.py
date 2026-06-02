"""
Test for nfc_reader.py helper.
All pyscard calls are mocked so no HardWare required
"""

import pytest
from unittest.mock import MagicMock, patch

def make_connection(data, sw1=0x90, sw2=0x00):
    """
    Build a mock pyscard connection.
    """
    connection = MagicMock()
    connection.transmit.return_value = (data, sw1, sw2)
    reader = MagicMock()
    reader.createConnection.return_value = connection
    return reader, connection

def test_read_nfc_tag_returns_uid():
    """
    Should return True.
    """
    uid_bytes = [0xAA, 0xBB, 0xCC, 0xDD]
    reader, _ = make_connection(uid_bytes)
    with patch("nfc.nfc_reader.readers", return_value=[reader]):
        from nfc.nfc_reader import read_nfc_tag
        result = read_nfc_tag()
    assert result == "AABBCCDD"

def test_read_nfc_tag_no_reader():
    """
    Should return None.
    """
    with patch("nfc.nfc_reader.readers", return_value=[]):
        from nfc.nfc_reader import read_nfc_tag
        result = read_nfc_tag()
    assert result is None

def test_read_nfc_tag_bad_status_word():
    """
    BAD SW (not 0x9000) should return None.
    """
    reader, _ = make_connection([], sw1 = 0x6A, sw2 = 0x82)
    with patch("nfc.nfc_reader.readers", return_value = [reader]):
        from nfc.nfc_reader import read_nfc_tag
        result = read_nfc_tag()
    assert result is None

def test_read_nfc_tag_no_card_exception():
    """
    NoCardException (no card present), should return 'WAITING'.
    """
    from smartcard.Exceptions import NoCardException
    reader =  MagicMock()
    connection =  MagicMock()
    connection.connect.side_effect = NoCardException("No card", 0)
    reader.createConnection.return_value = connection
    with patch("nfc.nfc_reader.readers",return_value=[reader]):
        from nfc.nfc_reader import read_nfc_tag
        result =  read_nfc_tag()
    assert result == "WAITING"

def test_read_nfc_tag_connection_exception():
    """
    CardConnectionException should return None.
    """
    from smartcard.Exceptions import CardConnectionException
    reader =  MagicMock()
    connection = MagicMock()
    connection.connect.side_effect = CardConnectionException()
    reader.createConnection.return_value = connection
    with patch("nfc.nfc_reader.readers", return_value=[reader]):
        from nfc.nfc_reader import read_nfc_tag
        result = read_nfc_tag()
    assert result is None
