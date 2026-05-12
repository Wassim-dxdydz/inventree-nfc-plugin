"""
Database models for the NFC plugin in InvenTree.

Defines the NFCTagLink model that establishes a many-to-one relationship between
NFC tag UIDs and InvenTree parts, tracking which user linked the tag and when.
"""

from django.conf import settings
from django.db import models


class NFCTagLink(models.Model):
    """Maps an NFC tag UID to an InvenTree Part"""

    uid = models.CharField(max_length=64, verbose_name="NFC Tag UID")

    part = models.ForeignKey(
        "part.Part",
        on_delete=models.CASCADE,
        related_name="nfc_tag",
        verbose_name="Linked Part",
    )

    active = models.BooleanField(default=True)
    linked_at = models.DateTimeField(auto_now_add=True)

    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        app_label = "nfc"
        ordering = ["-linked_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["uid"],
                condition=models.Q(active=True),
                name="unique_active_uid",
            ),
            models.UniqueConstraint(
                fields=["part"],
                condition=models.Q(active=True),
                name="unique_active_part",
            ),
        ]

    def save(self, *args, **kwargs):
        self.uid = (self.uid or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"NFC {self.uid} : {self.part.name}"
