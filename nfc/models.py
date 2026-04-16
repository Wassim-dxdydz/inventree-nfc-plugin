"""
Database models for the NFC plugin in InvenTree.

Defines the NFCTagLink model that establishes a many-to-one relationship between
NFC tag UIDs and InvenTree parts, tracking which user linked the tag and when.
"""

from django.db import models


class NFCTagLink(models.Model):
    """Maps an NFC tag UID to an InvenTree Part"""

    uid = models.CharField(max_length=64, unique=True, verbose_name="NFC Tag UID")

    part = models.ForeignKey(
        "part.Part",
        on_delete=models.CASCADE,
        related_name="nfc_tags",
        verbose_name="Linked Part",
    )

    linked_at = models.DateTimeField(auto_now_add=True)

    linked_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        app_label = "nfc"

    def __str__(self):
        return f"NFC {self.uid} : {self.part.name}"
