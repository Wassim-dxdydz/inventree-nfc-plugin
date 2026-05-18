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
