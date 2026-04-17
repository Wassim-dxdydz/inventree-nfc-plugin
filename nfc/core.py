"""NFC-based stock management plugin"""

import logging
from typing import ClassVar

from plugin import InvenTreePlugin
from plugin.mixins import (
    AppMixin,
    LocateMixin,
    SettingsMixin,
    UrlsMixin,
    UserInterfaceMixin,
)

from . import PLUGIN_VERSION

log = logging.getLogger(__name__)

class NFC(
    AppMixin, SettingsMixin, UrlsMixin, UserInterfaceMixin, InvenTreePlugin
):
    """NFC - custom InvenTree plugin."""

    # Plugin metadata
    TITLE = "NFC"
    NAME = "NFC"
    SLUG = "nfc"
    DESCRIPTION = "NFC-based stock management plugin"
    VERSION = PLUGIN_VERSION

    # Additional project information
    AUTHOR = "ABAHRI Wassim"
    WEBSITE = "https://wassimabahri.dev"
    LICENSE = "MIT"

    # Optionally specify supported InvenTree versions
    # MIN_VERSION = '0.18.0'
    # MAX_VERSION = '2.0.0'

    # Render custom UI elements to the plugin settings page
    ADMIN_SOURCE = "Settings.js:renderPluginSettings"

    # Plugin settings (from SettingsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/settings/
    SETTINGS: ClassVar[dict] = {
        "SCAN_TIMEOUT_SECONDS": {
            "name": "Scan timeout (seconds)",
            "description": "How long the UI waits for a scan session before timing out.",
            "validator": int,
            "default": 30,
        },
        "AGENT_BASE_URL": {
            "name": "Local NFC agent URL",
            "description": "Base URL of the workstation NFC agent.",
            "validator": str,
            "default": "http://127.0.0.1:8765",
        },
        "AUTO_REDIRECT": {
            "name": "Auto redirect on known tag",
            "description": "Redirect to the linked part page when a known tag is found.",
            "validator": bool,
            "default": True,
        },
        "ALLOW_LINK_FROM_SCAN": {
            "name": "Allow linking from scan flow",
            "description": "Allow users to link an unknown tag to a part from the scan flow.",
            "validator": bool,
            "default": True,
        },
    }

    # Custom URL endpoints (from UrlsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/urls/
    def setup_urls(self):
        """Configure custom URL endpoints for this plugin."""
        from django.urls import path
        from .views import NFCConfigView, NFCLinkView, NFCStockView, NFCTagView

        return [
            path("config/", NFCConfigView.as_view(), name="nfc-config"),
            path("tag/<str:uid>/", NFCTagView.as_view(), name="nfc-tag-detail"),
            path("link/", NFCLinkView.as_view(), name="nfc-link"),
            path("stock/", NFCStockView.as_view(), name="nfc-stock"),
        ]

    # User interface elements (from UserInterfaceMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/ui/

    # Custom UI panels
    def get_ui_panels(self, request, context: dict, **kwargs):
        """
        Show the NFC panel on Part detail and Stock Location pages
        """

        panels = []

        # Only display this panel for the 'part' target
        if context.get("target_model") in ["part", "stocklocation"]:
            panels.append({
                "key": "nfc-panel",
                "title": "NFC Scanner",
                "description": "Scan NFC tags to manage stock",
                "icon": "ti:wifi:outline",
                "source": self.plugin_static_file("Panel.js:renderNFCPanel"),
                "context": {
                    # Provide additional context data to the panel
                    "settings": self.get_settings_dict(),
                    "target_model": context.get("target_model"),
                    "target_id": context.get("target_id"),
                },
            })

        return panels

    # Custom dashboard items
    def get_ui_dashboard_items(self, request, context: dict, **kwargs):
        """
        Show NFC Dashboard item for staff users only.
        """

        # Example: only display for 'staff' users
        if not request.user or not request.user.is_staff:
            return []

        items = []

        items.append({
            "key": "nfc-dashboard",
            "title": "NFC Dashboard Item",
            "description": "Scan NFC tags to manage stock",
            "icon": "ti:wifi:outline",
            "source": self.plugin_static_file("Dashboard.js:renderNFCDashboardItem"),
            "context": {
                # Provide additional context data to the dashboard item
                "settings": self.get_settings_dict(),
            },
        })

        return items

    def get_ui_spotlight_actions(self, request, context, **kwargs):
        """
        Return spotlight search actions
        """

        return [
            {
                "key": "nfc-scan-action",
                "title": "Start NFC Scan",
                "description": "Scan an NFC tag to find or update a part",
                "icon": "ti:wifi:outline",
                "source": self.plugin_static_file("Spotlight.js:NFCSpotlightAction"),
            }
        ]
