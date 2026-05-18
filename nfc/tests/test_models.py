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

@pytest.mark.django_db
def test_uid_is_stripped_on_save(nfc_link_factory):
    """Leading/trailing whitespace must be stripped from UID."""
    link = nfc_link_factory(uid="  AABBCCDD  ")
    assert link.uid == "AABBCCDD"

@pytest.mark.django_db
def test_str_representation(nfc_link_factory):
    """__str__ should return 'NFC <uid> : <part name>'."""
    link = nfc_link_factory(uid="AABBCCDD")
    assert str(link) == f"NFC AABBCCDD : {link.part.name}"
