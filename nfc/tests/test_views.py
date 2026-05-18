"""
Tests for NFC plugin API views.
Uses DRF APIClient with forced authentication, so no full InvenTree server needed.
"""
import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIClient

@pytest.fixture()
def auth_client(django_user_model):
    user = django_user_model.objects.create_user(username="tester", password="pass")
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.fixture()
def staff_client(django_user_model):
    user = django_user_model.objects.create_user(username="staff", password="pass", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client

# GET /tag/<uid>/

@pytest.mark.django_db
def test_tag_view_found(auth_client, nfc_link_factory):
    link = nfc_link_factory(uid="AABBCCDD", active=True)
    res = auth_client.get(f"/plugin/nfc/tag/AABBCCDD/")
    assert res.status_code == 200
    assert res.data["found"] is True
    assert res.data["uid"] == "AABBCCDD"
    assert res.data["part_id"] == link.part.pk

@pytest.mark.django_db
def test_tag_view_not_found(auth_client):
    res = auth_client.get("/plugin/nfc/tag/UNKNOWN1/")
    assert res.status_code == 200
    assert res.data["found"] is False

@pytest.mark.django_db
def test_tag_view_uid_case_insensitive(auth_client, nfc_link_factory):
    """Lowercase UID in URL should match uppercase stored UID."""
    nfc_link_factory(uid="AABBCCDD", active=True)
    res = auth_client.get("/plugin/nfc/tag/aabbccdd/")
    assert res.data["found"] is True

# POST /link/

@pytest.mark.django_db
def test_link_view_success(auth_client, part_factory):
    part = part_factory(name="Resistor")
    res = auth_client.post("/plugin/nfc/link/", {"uid": "AABBCCDD", "part_id": part.pk})
    assert res.status_code == 201 or res.data.get("success") is True
    assert res.data["uid"] == "AABBCCDD"

@pytest.mark.django_db
def test_link_view_missing_fields(auth_client):
    res = auth_client.post("/plugin/nfc/link/", {"uid": "AABBCCDD"})
    assert res.status_code == 400

@pytest.mark.django_db
def test_link_view_duplicate_uid(auth_client, nfc_link_factory, part_factory):
    """Linking a UID already active on another part must return 409."""
    nfc_link_factory(uid="AABBCCDD", active=True)
    part2 = part_factory(name="Capacitor")
    res = auth_client.post("/plugin/nfc/link/", {"uid": "AABBCCDD", "part_id": part2.pk})
    assert res.status_code == 409

@pytest.mark.django_db
def test_link_view_part_already_linked(auth_client, nfc_link_factory):
    """A part that already has an active tag must return 409."""
    link = nfc_link_factory(uid="AABBCCDD", active=True)
    res = auth_client.post("/plugin/nfc/link/", {"uid": "11223344", "part_id": link.part.pk})
    assert res.status_code == 409

# DELETE /link/<uid>/

@pytest.mark.django_db
def test_unlink_view_success(staff_client, nfc_link_factory):
    nfc_link_factory(uid="AABBCCDD", active=True)
    res = staff_client.delete("/plugin/nfc/link/AABBCCDD/")
    assert res.status_code == 200
    assert res.data["success"] is True

@pytest.mark.django_db
def test_unlink_view_not_found(staff_client):
    res = staff_client.delete("/plugin/nfc/link/NOTEXIST/")
    assert res.status_code == 404

@pytest.mark.django_db
def test_unlink_requires_staff(auth_client, nfc_link_factory):
    """Non-staff users must be rejected with 403."""
    nfc_link_factory(uid="AABBCCDD", active=True)
    res = auth_client.delete("/plugin/nfc/link/AABBCCDD/")
    assert res.status_code == 403

# GET /tag/by-part/<id>/

@pytest.mark.django_db
def test_tag_by_part_found(auth_client, nfc_link_factory):
    link = nfc_link_factory(uid="AABBCCDD", active=True)
    res = auth_client.get(f"/plugin/nfc/tag/by-part/{link.part.pk}/")
    assert res.data["found"] is True
    assert res.data["uid"] == "AABBCCDD"

@pytest.mark.django_db
def test_tag_by_part_not_found(auth_client, part_factory):
    part = part_factory(name="Unlinked Part")
    res = auth_client.get(f"/plugin/nfc/tag/by-part/{part.pk}/")
    assert res.data["found"] is False
