"""Django config for the NFC plugin."""

from django.apps import AppConfig


class NFCConfig(AppConfig):
    """Config class for the NFC plugin."""

    name = "nfc"

    def ready(self):
        """This function is called whenever the NFC plugin is loaded."""
