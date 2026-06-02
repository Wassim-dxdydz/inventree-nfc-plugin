"""
Tests for NFC plugin API views.
Uses DRF APIClient with forced authentication, so no full InvenTree server needed.
"""
import pytest
from unittest.mock import MagicMock, patch
from rest_framework.test import APIClient, APIRequestFactory
from nfc.views import NFCTagView, NFCLinkView, NFCUnlinkView, NFCTagByPartView

@pytest.fixture()
def auth_user(db, django_user_model):
    return django_user_model.objects.create_user(username="tester", password="pass")

@pytest.fixture()
def staff_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="staff", password="pass", is_staff=True
    )

@pytest.fixture()
def rf():
    return APIRequestFactory()

# GET /tag/<uid>/

@pytest.mark.django_db
def test_tag_view_found(rf, auth_user, nfc_link_factory):
    nfc_link_factory(uid="AABBCCDD", active=True)
    request = rf.get("/")
    request.user = auth_user
    res = NFCTagView.as_view()(request, uid="AABBCCDD")
    res.render()
    assert res.status_code == 200
    assert res.data["found"] is True
    assert res.data["uid"] == "AABBCCDD"

@pytest.mark.django_db
def test_tag_view_not_found(rf, auth_user):
    request = rf.get("/")
    request.user = auth_user
    res = NFCTagView.as_view()(request, uid="UNKNOWN1")
    res.render()
    assert res.status_code == 200
    assert res.data["found"] is False

@pytest.mark.django_db
def test_tag_view_uid_case_insensitive(rf, auth_user, nfc_link_factory):
    nfc_link_factory(uid="AABBCCDD", active=True)
    request = rf.get("/")
    request.user = auth_user
    res = NFCTagView.as_view()(request, uid="aabbccdd")
    res.render()
    assert res.data["found"] is True

# POST /link/

@pytest.mark.django_db
def test_link_view_success(rf, auth_user, part_factory):
    part = part_factory(name="Resistor")
    request = rf.post("/", {"uid": "AABBCCDD", "part_id": part.pk}, format="json")
    request.user = auth_user
    res = NFCLinkView.as_view()(request)
    res.render()
    assert res.data.get("success") is True
    assert res.data["uid"] == "AABBCCDD"

@pytest.mark.django_db
def test_link_view_missing_fields(rf, auth_user):
    request = rf.post("/", {"uid": "AABBCCDD"}, format="json")
    request.user = auth_user
    res = NFCLinkView.as_view()(request)
    res.render()
    assert res.status_code == 400

@pytest.mark.django_db
def test_link_view_duplicate_uid(rf, auth_user, nfc_link_factory, part_factory):
    nfc_link_factory(uid="AABBCCDD", active=True)
    part2 = part_factory(name="Capacitor")
    request = rf.post("/", {"uid": "AABBCCDD", "part_id": part2.pk}, format="json")
    request.user = auth_user
    res = NFCLinkView.as_view()(request)
    res.render()
    assert res.status_code == 409

@pytest.mark.django_db
def test_link_view_part_already_linked(rf, auth_user, nfc_link_factory):
    link = nfc_link_factory(uid="AABBCCDD", active=True)
    request = rf.post("/", {"uid": "11223344", "part_id": link.part.pk}, format="json")
    request.user = auth_user
    res = NFCLinkView.as_view()(request)
    res.render()
    assert res.status_code == 409

# DELETE /link/<uid>/

@pytest.mark.django_db
def test_unlink_view_success(rf, staff_user, nfc_link_factory):
    nfc_link_factory(uid="AABBCCDD", active=True)
    request = rf.delete("/")
    request.user = staff_user
    res = NFCUnlinkView.as_view()(request, uid="AABBCCDD")
    res.render()
    assert res.status_code == 200
    assert res.data["success"] is True

@pytest.mark.django_db
def test_unlink_view_not_found(rf, staff_user):
    request = rf.delete("/")
    request.user = staff_user
    res = NFCUnlinkView.as_view()(request, uid="NOTEXIST")
    res.render()
    assert res.status_code == 404

@pytest.mark.django_db
def test_unlink_requires_staff(rf, auth_user, nfc_link_factory):
    nfc_link_factory(uid="AABBCCDD", active=True)
    request = rf.delete("/")
    request.user = auth_user
    res = NFCUnlinkView.as_view()(request, uid="AABBCCDD")
    res.render()
    assert res.status_code == 403

# GET /tag/by-part/<id>/

@pytest.mark.django_db
def test_tag_by_part_found(rf, auth_user, nfc_link_factory):
    link = nfc_link_factory(uid="AABBCCDD", active=True)
    request = rf.get("/")
    request.user = auth_user
    res = NFCTagByPartView.as_view()(request, part_id=link.part.pk)
    res.render()
    assert res.data["found"] is True
    assert res.data["uid"] == "AABBCCDD"

@pytest.mark.django_db
def test_tag_by_part_not_found(rf, auth_user, part_factory):
    part = part_factory(name="Unlinked Part")
    request = rf.get("/")
    request.user = auth_user
    res = NFCTagByPartView.as_view()(request, part_id=part.pk)
    res.render()
    assert res.data["found"] is False
