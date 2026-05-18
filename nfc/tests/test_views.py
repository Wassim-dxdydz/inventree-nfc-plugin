"""
Tests for NFC plugin API views.
Uses DRF APIClient with forced authentication — no full InvenTree server needed.
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
