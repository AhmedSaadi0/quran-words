from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from core.pagination import StandardPagination
from words.models import WordAyah

from .models import Ayah, Surah
from .serializers import AyahSerializer, AyahWithWordsSerializer, SurahSerializer


class SurahViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Surah.objects.all().order_by("id")
    serializer_class = SurahSerializer
    pagination_class = None
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name_ar", "name_en"]


class AyahViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ayah.objects.select_related("surah").all().order_by("surah", "ayah")
    serializer_class = AyahSerializer
    filterset_fields = ["surah", "ayah"]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["text_uthmani"]


class AyahWordsViewSet(viewsets.ReadOnlyModelViewSet):
    """Ayahs with nested words+morphology for the surah view."""

    serializer_class = AyahWithWordsSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Ayah.objects.select_related("surah").order_by("ayah")
        surah = self.request.query_params.get("surah")
        if surah:
            qs = qs.filter(surah_id=surah)
        return qs.prefetch_related(
            Prefetch(
                "wordayah_set",
                queryset=WordAyah.objects.select_related("word", "ayah")
                .order_by("position")
                .prefetch_related("wordmorphology__root", "wordmorphology__lemma"),
                to_attr="prefetched_wordayah",
            )
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        instances = page if page is not None else list(queryset)

        # جمع جذور الصفحة الحالية دفعة واحدة لحقن المعنى السريع (لا N+1)
        root_ids: set[int] = set()
        for ayah in instances:
            for wa in getattr(ayah, "prefetched_wordayah", None) or []:
                try:
                    wm = wa.wordmorphology
                except ObjectDoesNotExist:
                    continue
                if wm.root_id:
                    root_ids.add(wm.root_id)

        gloss_map = {}
        if root_ids:
            from roots.models import RootGloss

            gloss_map = {
                g.root_id_id: g for g in RootGloss.objects.filter(root_id__in=root_ids)
            }

        context = dict(self.get_serializer_context(), root_glosses=gloss_map)
        serializer = self.get_serializer(instances, many=True, context=context)
        data = serializer.data

        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)
