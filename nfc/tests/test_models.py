"""
Tests for NFCTagLink model logic.
Uses pytest-django with a minimal in-memory SQLite DB.
These run standalone without the full InvenTree stack.
"""
import pytest

@pytest.mark.django_db
def test_uid_is_uppercased_on_save(nfc_link_factory):
    """UID must be stored as uppercase regardless of input."""
    link = nfc_link_factory(uid="aabbccdd")
    assert link.uid == "AABBCCDD"
