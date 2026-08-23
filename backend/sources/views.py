from rest_framework import viewsets

from .models import Source
from .serializers import SourceSerializer


class SourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Source.objects.all().order_by("id")
    serializer_class = SourceSerializer
    pagination_class = None
