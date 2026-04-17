"""
API Views for the NFC plugin.
"""

from typing import ClassVar
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class NFCConfigView(APIView):
    permission_classes: ClassVar = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from .core import NFC

        plugin = NFC()
        return Response({
            "agent_base_url": plugin.get_setting("AGENT_BASE_URL"),
            "scan_timeout_seconds": int(plugin.get_setting("SCAN_TIMEOUT_SECONDS")),
            "auto_redirect": bool(plugin.get_setting("AUTO_REDIRECT")),
            "allow_link_from_scan": bool(plugin.get_setting("ALLOW_LINK_FROM_SCAN")),
        })

class NFCTagView(APIView):
    """
    GET /tag/<uid>/
    Check if an NFC tag UID is linked to a Part.
    """

    permission_classes: ClassVar = [permissions.IsAuthenticated]

    def get(self, request, uid, *args, **kwargs):
        """
        GET part linked to the NFC tag
        """

        from .models import NFCTagLink

        uid = uid.strip().upper()

        try:
            link = NFCTagLink.objects.get(uid=uid.upper())
            part = link.part
            return Response({
                "found": True,
                "uid": uid.upper(),
                "part_id": part.pk,
                "part_name": part.name,
                "part_description": part.description,
                "total_stock": float(part.total_stock),
                "part_url": f"/part/{part.pk}/",
            })
        except NFCTagLink.DoesNotExist:
            return Response({"found": False, "uid": uid.upper()})

class NFCLinkView(APIView):
    """
    POST /link/
    Link an NFC tag UID to an InvenTree Part.
    Body: { "uid": "AABBCCDD", "part_id": 42 }
    """

    permission_classes: ClassVar = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from part.models import Part
        from .models import NFCTagLink

        uid = str(request.data.get("uid", "")).strip().upper()
        part_id = request.data.get("part_id")

        if not uid or not part_id:
            return Response(
                {"error": "Both 'uid' and 'part_id' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            part = Part.objects.get(pk=part_id)
        except Part.DoesNotExist:
            return Response(
                {"error": f"Part with id {part_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        link, created = NFCTagLink.objects.update_or_create(
            uid=uid,
            defaults={
                "part": part,
                "linked_by": request.user,
                "active": True,
            },
        )

        return Response({
            "success": True,
            "created": created,
            "uid": link.uid,
            "part_id": part.pk,
            "part_name": part.name,
        })

class NFCStockView(APIView):
    """
    POST /stock/
    Add or remove stock for a part linked to an NFC tag.
    Body: { "uid": "AABBCCDD", "quantity": 5, "action": "add" | "remove", "notes": "optional" }
    """

    permission_classes: ClassVar = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from stock.models import StockItem
        from .models import NFCTagLink

        uid = str(request.data.get("uid", "")).strip().upper()
        stock_item_id = request.data.get("stock_item_id")
        action = str(request.data.get("action", "add")).strip().lower()
        notes = str(request.data.get("notes", f"NFC {action}")).strip()

        try:
            quantity = float(request.data.get("quantity", 0))
        except (TypeError, ValueError):
            return Response({"error": "Quantity must be a number."}, status=status.HTTP_400_BAD_REQUEST)

        if not uid or not stock_item_id or quantity <= 0:
            return Response(
                {"error": "UID and quantity > 0 are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            link = NFCTagLink.objects.select_related("part").get(uid=uid)
        except NFCTagLink.DoesNotExist:
            return Response(
                {"error": "Tag not linked to any part."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stock_item = StockItem.objects.get(
                pk=stock_item_id,
                part=link.part,
                deleted=False,
            )
        except StockItem.DoesNotExist:
            return Response(
                {"error": F"Matching stock item not found for linked part {link.part.name}."},
                status=status.HTTP_404_NOT_FOUND
            )

        if action == "remove":
            if stock_item.quantity < quantity:
                return Response(
                    {"error": f"Not enough stock. Available: {stock_item.quantity}."},
                    status=status.HTTP_400_BAD_REQUEST,
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
