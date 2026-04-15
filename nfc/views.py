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

class NFCTagView(APIView):
    """
    GET /tag/<uid>/ : check if an NFC tag is linked to a Part.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, uid, *args, **kwargs):
        """
        GET part linked to the NFC tag
        """

        from .models import NFCTagLink
        try:
            link = NFCTagLink.objects.get(uid=uid.upper())
            part = link.part
            return Response({
                "uid": True,
                "part_id": uid.upper(),
                "part_id": part.pk,
                "part_name": part.name,
                "part_description": part.description,
                "total_stock": float(part.total_stock),
                "part_url": f"/part/{part.pk}/",
            })
        except NFCTagLink.DoesNotExist:
            return Response({
                "found": False,
                "uid": uid.upper(),
            })
