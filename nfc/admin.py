"""Admin site configuration for the NFC plugin."""

from django.contrib import admin

from .models import NFCTagLink


@admin.register(NFCTagLink)
class NFCTagLinkAdmin(admin.ModelAdmin):
    """Admin interface for the NFCTagLink"""

    list_display = (
        "uid",
        "part",
        "linked_at",
        "linked_by"
    )

    list_filter = (
        "uid",
    )

    search_fields = (
        "uid",
        "part__name"
    )
