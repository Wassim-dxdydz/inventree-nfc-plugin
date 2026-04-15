"""NFC-based stock management plugin"""

import threading
import logging
import time

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
    AppMixin, LocateMixin, SettingsMixin, UrlsMixin, UserInterfaceMixin, InvenTreePlugin
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
    WEBSITE = "https://my-project-url.com"
    LICENSE = "MIT"

    # Optionally specify supported InvenTree versions
    # MIN_VERSION = '0.18.0'
    # MAX_VERSION = '2.0.0'

    # Render custom UI elements to the plugin settings page
    ADMIN_SOURCE = "Settings.js:renderPluginSettings"

    # Plugin settings (from SettingsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/settings/
    SETTINGS = {
        "POLL_INTERVAL": {
            "name" : "Poll interval (seconds)",
            "description" : "How often to poll the NFC reader fo a new tag.",
            "validator" : int,
            "default" : 1,
        },
        "AUTO_REDIRECT" : {
            "name" : "auto-redirect on scan",
            "description" : "Automatically navigate to the Part page when a known tag is scanned",
            "validator" : bool,
            "default" : True,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start_reader_thread()

    # NFC Reader Thread
    def _start_reader_thread(self):
        """
        Start the background NFC polling thread if not already running.
        """
        if self._reader_thread and self._reader_thread.is_alive():
            return
        self._stop_event.clear()
        self._reader_thread =  threading.Thread(
            target=self._reader_loop,
            daemon=True,
            name="nfc-reader-thread",
        )
        self._reader_thread.start()
        log.info("NFC reader background thread started")

    def _reader_loop(self):
        """
        Continuously poll the NFC reader and store the last scanned UID.
        """
        try:
            from .nfc_reader import read_nfc_tag
        except ImportError:
            log.warning("pyscard not installed - NFC reader thread disabled")
            return

        last_uid = None
        while not self._stop_event.is_set():
            try:
                uid = read_nfc_tag
                if uid and uid != "WAITING" and uid != last_uid:
                    with NFC._lock:
                        NFC._last_scanned_uid = uid
                    last_uid = uid
                    log.info(f"NFC scan detected : {uid}")
                if not uid or uid == "WAITING":
                    last_uid =  None
                time.sleep(1)
            except Exception as e:
                log.error(f"NFC reader loop error : {e}")
                time.sleep(2)

    # Perform custom locate operations (from LocateMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/locate/
    def locate_stock_item(self, item_id: int):
        """Attempt to locate a particular StockItem."""
        log.debug(f"locate_stock_item called for item {item_id}")

    def locate_stock_location(self, location_id: int):
        """Attempt to locate a particular StockLocation."""
        log.debug(f"locate_stock_location called for location {location_id}")

    # Custom URL endpoints (from UrlsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/urls/
    def setup_urls(self):
        """Configure custom URL endpoints for this plugin."""
        from django.urls import path

        from .views import ExampleView

        return [
            # Provide path to a simple custom view - replace this with your own views
            path("example/", ExampleView.as_view(), name="example-view"),
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
        """Return a list of custom spotlight actions to be made available."""
        return [
            {
                "key": "sample-spotlight-action",
                "title": "Hello Action",
                "description": "Hello from NFC",
                "icon": "ti:heart-handshake:outline",
                "source": self.plugin_static_file("Spotlight.js:NFCSpotlightAction"),
            }
        ]
