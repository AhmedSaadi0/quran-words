from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from core.utils import normalize_query

from .models import Derivative, Masdar
from .serializers import DerivativeSerializer, MasdarSerializer


class MasdarViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Masdar.objects.select_related("root_ref")
        .all()
        .order_by("-is_attested", "-confidence", "masdar_plain")
    )
    serializer_class = MasdarSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["root_ref", "form", "is_attested", "source"]
    search_fields = ["masdar_ar", "masdar_plain", "pattern", "root_text"]
    ordering_fields = ["confidence", "masdar_plain"]

    def get_queryset(self):
        qs = super().get_queryset()
        root = self.request.query_params.get("root")
        q = self.request.query_params.get("q") or self.request.query_params.get(
            "search"
        )
        if root:
            nq = normalize_query(root)
            qs = qs.filter(Q(root_text=root) | Q(root_text__icontains=nq))
        if q:
            nq = normalize_query(q)
            qs = qs.filter(
                Q(masdar_ar__icontains=q)
                | Q(masdar_plain__icontains=nq)
                | Q(masdar_plain__icontains=q)
            )
        return qs


class DerivativeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Derivative.objects.select_related("root_ref", "example_word")
        .all()
        .order_by("-is_quranic", "-camel_valid", "pattern")
    )
    serializer_class = DerivativeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["root_ref", "pattern", "derivative_type", "is_quranic", "pos"]
    search_fields = ["form_ar", "form_plain", "pattern", "derivative_type", "root_text"]
    ordering_fields = ["form_plain"]

    def get_queryset(self):
        qs = super().get_queryset()
        root = self.request.query_params.get("root")
        q = self.request.query_params.get("q") or self.request.query_params.get(
            "search"
        )
        if root:
            nq = normalize_query(root)
            qs = qs.filter(Q(root_text=root) | Q(root_text__icontains=nq))
        if q:
            nq = normalize_query(q)
            qs = qs.filter(Q(form_ar__icontains=q) | Q(form_plain__icontains=nq))
        return qs
