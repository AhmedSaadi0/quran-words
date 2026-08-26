from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from core.utils import normalize_query
from derivatives.models import Derivative, Masdar
from derivatives.serializers import DerivativeSerializer, MasdarSerializer
from morphology.models import WordMorphology
from morphology.serializers import WordMorphologySerializer
from quran.serializers import AyahSerializer
from roots.models import RootMeaning
from roots.serializers import RootMeaningSerializer

from .models import Word, WordAyah
from .serializers import WordAyahSerializer, WordSerializer


class WordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Word.objects.all().order_by("id")
    serializer_class = WordSerializer
    filter_backends = [OrderingFilter]
    search_fields = ["text", "text_clean", "translation", "transliteration"]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("search") or self.request.query_params.get(
            "q"
        )
        root = self.request.query_params.get("root")
        surah = self.request.query_params.get("surah")

        if q:
            nq = normalize_query(q)
            qs = qs.filter(
                Q(text__icontains=q)
                | Q(text_clean__icontains=q)
                | Q(text_clean__icontains=nq)
                | Q(text_plain__icontains=nq)
                | Q(translation__icontains=q)
            )

        if root:
            # Words whose occurrences carry this exact root; if none, fall back to plain-text match.
            by_root = Word.objects.filter(
                wordayah__wordmorphology__root__root=root
            ).distinct()
            qs = (
                by_root
                if by_root.exists()
                else qs.filter(text_clean__icontains=normalize_query(root))
            )

        if surah:
            qs = qs.filter(wordayah__ayah__surah_id=surah).distinct()

        return qs.distinct()


class WordAyahViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WordAyah.objects.select_related("word", "ayah", "ayah__surah").order_by(
        "ayah__surah", "ayah__ayah", "position"
    )
    serializer_class = WordAyahSerializer
    filterset_fields = ["ayah", "word"]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["position"]

    def get_queryset(self):
        qs = super().get_queryset()
        surah = self.request.query_params.get("surah")
        ayah = self.request.query_params.get("ayah")
        word = self.request.query_params.get("word")
        pos = self.request.query_params.get("pos")
        root = self.request.query_params.get("root")

        if surah:
            qs = qs.filter(ayah__surah_id=surah)
        if ayah:
            qs = qs.filter(ayah__ayah=ayah)
        if word:
            qs = qs.filter(word__text__icontains=word)
        if pos:
            qs = qs.filter(wordmorphology__pos=pos)
        if root:
            qs = qs.filter(wordmorphology__root__root=root)

        return qs.select_related("word", "ayah", "ayah__surah").prefetch_related(
            "wordmorphology__root", "wordmorphology__lemma"
        )


@api_view(["GET"])
def word_detail(request, pk):
    """Full detail for a word: word + occurrences + morphology + masadir + root derivatives."""
    try:
        word = Word.objects.get(pk=pk)
    except Word.DoesNotExist:
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    word_data = WordSerializer(word).data

    occurrences = (
        WordAyah.objects.filter(word=word)
        .select_related("ayah", "ayah__surah")
        .order_by("ayah__surah", "ayah__ayah")
    )

    occ_data = []
    for wa in occurrences[:20]:
        wm = WordMorphology.objects.filter(word_ayah=wa).first()
        occ_data.append(
            {
                "word_ayah_id": wa.id,
                "ayah": AyahSerializer(wa.ayah).data,
                "position": wa.position,
                "location": wa.location,
                "morphology": (WordMorphologySerializer(wm).data if wm else None),
            }
        )

    wm_first = (
        WordMorphology.objects.filter(word_ayah__word=word)
        .select_related("root")
        .first()
    )
    root_id = wm_first.root_id if wm_first else None
    root_text = wm_first.root.root if wm_first and wm_first.root else None

    ai_summary = None
    if root_id:
        from roots.models import RootAiSummary

        ai_summary = RootAiSummary.objects.filter(root_id=root_id).first()

    masadir = []
    derivatives = []
    meanings = []
    if root_id:
        masadir = MasdarSerializer(
            Masdar.objects.filter(root_ref_id=root_id).order_by(
                "-is_attested", "-confidence"
            )[:20],
            many=True,
        ).data
        derivatives = DerivativeSerializer(
            Derivative.objects.filter(root_ref_id=root_id).order_by("-is_quranic")[:20],
            many=True,
        ).data
        meanings = RootMeaningSerializer(
            RootMeaning.objects.filter(root_id=root_id)[:5], many=True
        ).data

    return Response(
        {
            "word": word_data,
            "root": (
                {
                    "id": root_id,
                    "root": root_text,
                    "ai_summary_ar": ai_summary.summary_ar if ai_summary else None,
                    "ai_summary_model": ai_summary.model if ai_summary else None,
                    "ai_summary_generated_at": ai_summary.generated_at
                    if ai_summary
                    else None,
                }
                if root_id
                else None
            ),
            "occurrences": occ_data,
            "occurrences_count": occurrences.count(),
            "masadir": masadir,
            "derivatives": derivatives,
            "meanings": meanings,
        }
    )
