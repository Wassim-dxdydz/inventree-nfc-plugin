"""
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class NFCScanStatusView(APIView):
    """
    """

    # You can control which users can access this view using DRF permissions
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        """
