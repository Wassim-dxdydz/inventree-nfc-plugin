"""
API Views for the NFC plugin
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class NFCScanStatusView(APIView):
    """
    GET - Returns the last scanned NFC UID and clears it.
    The frontend polls this every second while scanning is active
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        GET the last scanned UID
        """

        from .core import NFC
        with NFC._lock:
            uid = NFC._last_scanned_uid
            NFC._last_scanned_uid = None
        if uid:
            return Response({
                "found": True,
                "uid": uid,
            })
        return Response({
            "found": False,
            "uid": None
        })
