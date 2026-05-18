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

@pytest.mark.django_db
def test_unique_active_uid_constraint(nfc_link_factory, part_factory):
    """Two active links with the same UID must be rejected."""
    from django.db import IntegrityError
    part1 = part_factory(name="Part A")
    part2 = part_factory(name="Part B")
    nfc_link_factory(uid="AABBCCDD", part=part1, active=True)
    with pytest.raises(IntegrityError):
        nfc_link_factory(uid="AABBCCDD", part=part2, active=True)

@pytest.mark.django_db
def test_inactive_uid_allows_reuse(nfc_link_factory, part_factory):
    """An inactive link's UID can be reused for a new active link."""
    part1 = part_factory(name="Part A")
    part2 = part_factory(name="Part B")
    nfc_link_factory(uid="AABBCCDD", part=part1, active=False)
    link2 = nfc_link_factory(uid="AABBCCDD", part=part2, active=True)
    assert link2.pk is not None

@pytest.mark.django_db
def test_unique_active_part_constraint(nfc_link_factory, part_factory):
    """A part can only have one active NFC tag at a time."""
    from django.db import IntegrityError
    part = part_factory(name="Part A")
    nfc_link_factory(uid="AABBCCDD", part=part, active=True)
    with pytest.raises(IntegrityError):
        nfc_link_factory(uid="11223344", part=part, active=True)
