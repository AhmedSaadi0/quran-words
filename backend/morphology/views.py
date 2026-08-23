from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from .models import Lemma, WordMorphology
from .serializers import LemmaSerializer, WordMorphologySerializer


class LemmaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lemma.objects.all().order_by("lemma_ar")
    serializer_class = LemmaSerializer
    filter_backends = [SearchFilter]
    search_fields = ["lemma_ar", "lemma_bw"]


class WordMorphologyViewSet(viewsets.ReadOnlyModelViewSet):
    """Raw morphology analyses with optional root/pos filters."""

    queryset = (
        WordMorphology.objects.select_related("word_ayah__ayah__surah")
        .prefetch_related("root", "lemma")
        .all()
    )
    serializer_class = WordMorphologySerializer
    filterset_fields = ["pos", "root"]
