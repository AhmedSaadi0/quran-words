from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

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
