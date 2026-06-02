import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def part_factory(db):
    """Creates a minimal InvenTree Part for testing."""
    from part.models import Part, PartCategory

    def make_part(name="Test Part", description="A test part"):
        category, _ = PartCategory.objects.get_or_create(name="Test Category")
        return Part.objects.create(
            name=name,
            description=description,
            category=category,
            is_template=False,
        )

    return make_part


@pytest.fixture
def nfc_link_factory(db, part_factory):
    """Creates an NFCTagLink for testing."""
    from nfc.models import NFCTagLink

    def make_link(uid="AABBCCDD", part=None, active=True):
        if part is None:
            part = part_factory()
        return NFCTagLink.objects.create(uid=uid, part=part, active=active)

    return make_link