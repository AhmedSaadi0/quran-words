from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from derivatives.models import Derivative, Masdar

from .models import Root, RootGloss, RootMeaning
from .serializers import RootMeaningSerializer, RootSerializer


def attach_glosses(roots: list) -> None:
    """يربط المعنى السريع بنسخ Root دفعة واحدة (يستدعى قبل التسلسل)."""
    ids = [r.id for r in roots]
    if not ids:
        return
    gloss_map = {g.root_id_id: g for g in RootGloss.objects.filter(root_id__in=ids)}
    for r in roots:
        r._gloss = gloss_map.get(r.id)


def enrich_roots(roots: list) -> None:
    """يربط العدادات والمعنى السريع بنسخ Root دفعة واحدة."""
    if not roots:
        return
    ids = [r.id for r in roots]

    masadir_counts = {
        row["root_ref_id"]: row["cnt"]
        for row in (
            Masdar.objects.filter(root_ref_id__in=ids)
            .values("root_ref_id")
            .annotate(cnt=Count("id"))
        )
    }
    deriv_counts = {
        row["root_ref_id"]: row["cnt"]
        for row in (
            Derivative.objects.filter(root_ref_id__in=ids)
            .values("root_ref_id")
            .annotate(cnt=Count("id"))
        )
    }
    meanings_counts = {
        row["root_id"]: row["cnt"]
        for row in (
            RootMeaning.objects.filter(root_id__in=ids)
            .values("root_id")
            .annotate(cnt=Count("id"))
        )
    }
    gloss_map = {g.root_id_id: g for g in RootGloss.objects.filter(root_id__in=ids)}

    for r in roots:
        r.masadir_count = masadir_counts.get(r.id, 0)
        r.derivatives_count = deriv_counts.get(r.id, 0)
        r.meanings_count = meanings_counts.get(r.id, 0)
        r._gloss = gloss_map.get(r.id)


class RootViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RootSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["root"]
    ordering_fields = ["root", "id"]

    def get_queryset(self):
        qs = Root.objects.all().order_by("root")
        q = self.request.query_params.get("search") or self.request.query_params.get(
            "q"
        )
        if q:
            from core.utils import normalize_query

            nq = normalize_query(q)
            qs = qs.filter(Q(root__icontains=q) | Q(root__icontains=nq))
        return qs

    def list(self, request, *args, **kwargs):
        # ترقيم يدوي حتى نربط العدادات والـ gloss بالكائنات قبل التسلسل
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        instances = page if page is not None else list(queryset)

        enrich_roots(instances)

        serializer = self.get_serializer(instances, many=True)
        results = serializer.data
        if page is not None:
            return self.get_paginated_response(results)
        return Response(results)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        enrich_roots([instance])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class RootMeaningViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RootMeaning.objects.select_related("root").all()
    serializer_class = RootMeaningSerializer
    filterset_fields = ["root_id"]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["definition", "book_name"]

    def get_queryset(self):
        qs = super().get_queryset()
        root = self.request.query_params.get("root")
        root_id = self.request.query_params.get("root_id")
        q = self.request.query_params.get("q") or self.request.query_params.get(
            "search"
        )
        if root:
            qs = qs.filter(root__root=root)
        if root_id:
            qs = qs.filter(root_id=root_id)
        if q:
            qs = qs.filter(definition__icontains=q)
        return qs
