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
        return Response({"found": False, "uid": None})


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
        from part.models import Part

        from .models import NFCTagLink

        uid = request.data.get("uid", "").strip().upper()
        part_id = request.data.get("part_id")

        if not uid or not part_id:
            return Response(
                {"error": "Both 'uid' and 'part_id' are required. "}, status=400
            )

        try:
            part = Part.objects.get(pk=part_id)
        except Part.DoesNotExist:
            return Response({"error": f"Part with id {part_id} not found."}, status=404)

        link, created = NFCTagLink.objects.update_or_create(
            uid=uid,
            defaults={
                "part": part,
                "linked_by": request.user,
            },
        )

        return Response({
            "success": True,
            "created": created,
            "uid": uid,
            "part_id": part.pk,
            "part_name": part.name,
        })


class NFCStockView(APIView):
    """
    POST /stock/ : add or remove stock for a linked NFC tag.
    Body: { "uid": "AABBCCDD", "quantity": 5, "action": "add" | "remove", "notes": "optional" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from stock.models import StockItem

        from .models import NFCTagLink

        uid = request.data.get("uid", "").strip().upper()
        action = request.data.get("action", "add")
        notes = request.data.get("notes", f"NFC {action}")

        try:
            quantity = float(request.data.get("quantity", 0))
        except (TypeError, ValueError):
            return Response({"error": "Quantity must be a number."}, status=400)

        if not uid or quantity <= 0:
            return Response({"error": "UID and Quantity > 0 are required."}, status=400)

        try:
            link = NFCTagLink.objects.get(uid=uid)
        except NFCTagLink.DoesNotExist:
            return Response({"error": "Tag not linked to any Part."}, status=404)

        stock_items = StockItem.objects.filter(part=link.part, deleted=False)

        if not stock_items.exists():
            return Response(
                {"error": f"No stock items found for aprt '{link.part.name}'."},
                status=404,
            )

        stock_item = stock_items.first()

        if action == "remove":
            if stock_item.quantity < quantity:
                return Response(
                    {"error": f"Not enough stock. Available: {stock_item.quantity}."},
                    status=400,
                )
            stock_item.take_stock(quantity, request.user, notes=notes)
        else:
            stock_item.add_stock(quantity, request.user, notes=notes)

        stock_item.refresh_from_db()

        return Response({
            "success": True,
            "part_name": link.part.name,
            "action": action,
            "quantity_changed": quantity,
            "new_stock": float(stock_item.quantity),
        })
