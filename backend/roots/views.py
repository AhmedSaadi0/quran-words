from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from derivatives.models import Derivative, Masdar

from .models import Root, RootMeaning
from .serializers import RootMeaningSerializer, RootSerializer


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
        response = super().list(request, *args, **kwargs)
        results = response.data.get("results")
        if not results:
            return response

        ids = [item["id"] for item in results]

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

        for item in results:
            rid = item["id"]
            item["masadir_count"] = masadir_counts.get(rid, 0)
            item["derivatives_count"] = deriv_counts.get(rid, 0)
            item["meanings_count"] = meanings_counts.get(rid, 0)

        return response


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
