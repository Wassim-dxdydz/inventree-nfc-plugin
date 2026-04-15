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

class NFCLinkView(APIView):
    """
    POST /link/ : link an NFC Tag UID to an InvenTree Part.
    Body: { "uid": "AABBCCDD", "part_id": 42 }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from .models import NFCTagLink
        from part.models import Part

        uid = request.data.get("uid", "").strip().upper()
        part_id = request.data.get("part_id")

        if not uid or not part_id:
            return Response(
                {"error": "Both 'uid' and 'part_id' are required"},
                status=400
                )

        try:
            part = Part.objects.get(pk = part_id)
        except Part.DoesNotExist:
            return Response(
                {"error": f"Part with id {part_id} not found"},
                status=400
                )

        link, created =  NFCTagLink.objects.update_or_create(
            uid = uid,
            defaults={
                "part": part,
                "linked_by":request.user,
            },
        )

        return Response({
            "success": True,
            "created": created,
            "uid": uid,
            "part_id":part.pk,
            "part_name": part.name,
        })
