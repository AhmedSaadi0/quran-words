from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
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
    filterset_fields = [
        "surah",
        "ayah",
        "juz",
        "hizb",
        "rub_el_hizb",
        "page_number",
        "manzil_number",
        "ruku_number",
        "sajdah_number",
    ]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["text_uthmani", "text_uthmani_plain"]
    ordering_fields = [
        "surah",
        "ayah",
        "juz",
        "hizb",
        "rub_el_hizb",
        "page_number",
        "manzil_number",
        "ruku_number",
    ]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q")
        if q:
            from core.utils import normalize_query
            from django.db.models import Q

            nq = normalize_query(q)
            qs = qs.filter(
                Q(text_uthmani__icontains=q)
                | Q(text_uthmani__icontains=nq)
                | Q(text_uthmani_plain__icontains=nq)
            )
        return qs


class AyahWordsViewSet(viewsets.ReadOnlyModelViewSet):
    """Ayahs with nested words+morphology for the surah view."""

    serializer_class = AyahWithWordsSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = [
        "juz",
        "hizb",
        "rub_el_hizb",
        "page_number",
        "manzil_number",
        "ruku_number",
    ]
    ordering_fields = ["surah", "ayah", "page_number", "juz", "hizb"]

    def get_queryset(self):
        qs = Ayah.objects.select_related("surah").order_by("surah", "ayah")
        surah = self.request.query_params.get("surah")
        root = self.request.query_params.get("root")
        juz = self.request.query_params.get("juz")
        hizb = self.request.query_params.get("hizb")
        rub = self.request.query_params.get(
            "rub_el_hizb"
        ) or self.request.query_params.get("rub")
        # page_number = Mushaf page (1..604) — strictly separate from pagination ?page=
        page_number = self.request.query_params.get("page_number")
        if surah:
            qs = qs.filter(surah_id=surah)
        if juz:
            qs = qs.filter(juz=juz)
        if hizb:
            qs = qs.filter(hizb=hizb)
        if rub:
            qs = qs.filter(rub_el_hizb=rub)
        if page_number:
            qs = qs.filter(page_number=page_number)
        if root:
            qs = qs.filter(wordayah__wordmorphology__root__root=root).distinct()
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
        # Direct ORM for Mushaf pages: when page_number is present, bypass pagination
        # and return the exact list for that printed page (no count/next/previous).
        is_mushaf_query = bool(request.query_params.get("page_number"))
        queryset = self.filter_queryset(self.get_queryset())
        # Keep standard offset pagination when not a Mushaf query (e.g. root/text search)
        page = None
        if not is_mushaf_query:
            page = self.paginate_queryset(queryset)
        instances = page if page is not None else list(queryset)

        # جمع جذور الصفحة الحالية دفعة واحدة لحقن الملخص الذكي والمعنى السريع (لا N+1)
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
        ai_summary_map = {}
        if root_ids:
            from roots.models import RootAiSummary, RootGloss

            gloss_map = {
                g.root_id_id: g for g in RootGloss.objects.filter(root_id__in=root_ids)
            }
            ai_summary_map = {
                a.root_id_id: a
                for a in RootAiSummary.objects.filter(root_id__in=root_ids)
            }

        context = dict(
            self.get_serializer_context(),
            root_glosses=gloss_map,
            root_ai_summaries=ai_summary_map,
        )
        serializer = self.get_serializer(instances, many=True, context=context)
        data = serializer.data

        if is_mushaf_query:
            return Response(data)
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)


# ------------------------------------------------------------------ #
# Mushaf pages — true Madina 604 boundaries from ayat.page_number
# ------------------------------------------------------------------ #


@api_view(["GET"])
def mushaf_pages(request):
    """List all 604 Mushaf pages with start/end boundaries.

    Cached 24h via frontend revalidate. Each entry:
    {page_number, start_surah, start_ayah, end_surah, end_ayah, ayah_count, juz, hizb}
    """
    # Python grouping for accurate start/end (ordered by page_number, surah, ayah)
    with connection.cursor() as cur:
        cur.execute(
            "SELECT page_number, surah, ayah, juz, hizb FROM ayat ORDER BY page_number, surah, ayah"
        )
        rows = cur.fetchall()
    from collections import defaultdict

    pages: dict[int, list[tuple[int, int, int, int]]] = defaultdict(list)
    for pn, s, a, j, h in rows:
        pages[pn].append((s, a, j, h))
    result = []
    for pn in sorted(pages.keys()):
        lst = pages[pn]
        s_s, a_s, j_s, h_s = lst[0]
        s_e, a_e, j_e, h_e = lst[-1]
        result.append(
            {
                "page_number": pn,
                "start_surah": s_s,
                "start_ayah": a_s,
                "end_surah": s_e,
                "end_ayah": a_e,
                "ayah_count": len(lst),
                "juz": j_s,
                "hizb": h_s,
            }
        )
    return Response(result)


@api_view(["GET"])
def mushaf_page_detail(request, page_number: int):
    """Single Mushaf page: boundaries + ayat list (with pagination optional)."""
    try:
        pn = int(page_number)
    except (TypeError, ValueError):
        return Response({"detail": "page_number must be 1..604"}, status=400)
    if not 1 <= pn <= 604:
        return Response({"detail": "page_number must be 1..604"}, status=404)
    qs = (
        Ayah.objects.filter(page_number=pn)
        .select_related("surah")
        .order_by("surah", "ayah")
    )
    # optional: return paginated ayat? For now return all ayat on page (max ~15)
    # Reuse AyahSerializer for light payload; client can fetch ayah-words separately
    with connection.cursor() as cur:
        cur.execute(
            "SELECT page_number, surah, ayah FROM ayat WHERE page_number=%s ORDER BY surah, ayah LIMIT 1",
            [pn],
        )
        start = cur.fetchone()
        cur.execute(
            "SELECT page_number, surah, ayah FROM ayat WHERE page_number=%s ORDER BY surah DESC, ayah DESC LIMIT 1",
            [pn],
        )
        end = cur.fetchone()
    boundary = {}
    if start and end:
        boundary = {
            "page_number": pn,
            "start_surah": start[1],
            "start_ayah": start[2],
            "end_surah": end[1],
            "end_ayah": end[2],
            "ayah_count": qs.count(),
        }
    data = AyahSerializer(qs, many=True).data
    return Response({"page": boundary, "ayat": data})
