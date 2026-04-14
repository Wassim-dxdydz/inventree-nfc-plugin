"""
Serializers for NFC tag REST API endpoints in InvenTree.

Provides serialization of NFC tag links and associated part data for API responses.
"""

from rest_framework import serializers
from .models import NFCTagLink


class NFCTagLinkSerializer(serializers.Serializer):
    """
    Serializer for NFCTagLink model.

    Converts NFCTagLink database records to JSON for API responses, including
    nested part information (name, description, total stock) and a link to the part detail page.
    """

    part_name = serializers.CharField(source = 'part.name', read_only = True)
    part_description = serializers.CharField(source = 'part.description', read_only =  True)
    total_stock =  serializers.FloatField(source = 'part.total_stock', read_only = True)
    part_url = serializers.SerializerMethodField()

    class Meta:
        model = NFCTagLink
        fields = [
            'id',
            'uid',
            'part',
            'part_name',
            'part_description',
            'total_stock',
            'part_url',
            'linked_at'
        ]
    
    def get_part_url(self, obj):
        return f'/part/{obj.part.pk}/'
