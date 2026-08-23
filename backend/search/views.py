from django.db import connection
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.utils import normalize_query
from derivatives.models import Derivative, Masdar
from derivatives.serializers import DerivativeSerializer, MasdarSerializer
from quran.models import Ayah
from quran.serializers import AyahSerializer
from roots.models import Root
from roots.serializers import RootSerializer
from words.models import Word
from words.serializers import WordSerializer


@api_view(["GET"])
def unified_search(request):
    """
    ?q=كتب&type=all|root|masdar|derivative|word
    Returns {query, normalized, roots, masadir, derivatives, words, ayat}.
    Priority: roots first, then masadir, then words.
    """
    q = request.query_params.get("q", "").strip()
    if not q or len(q) < 2:
        return Response(
            {"detail": "q must be at least 2 chars"}, status=status.HTTP_400_BAD_REQUEST
        )

    nq = normalize_query(q)
    type_filter = request.query_params.get("type", "all")

    data = {
        "query": q,
        "normalized": nq,
        "roots": [],
        "masadir": [],
        "derivatives": [],
        "words": [],
        "ayat": [],
    }

    # Roots — with batched counts (N+1 fix: two grouped queries total)
    if type_filter in ("all", "root"):
        roots = list(
            Root.objects.filter(Q(root__icontains=q) | Q(root__icontains=nq))[:10]
        )
        data["roots"] = RootSerializer(roots, many=True).data
        root_ids = [r.id for r in roots]
        if root_ids:
            masadir_counts = {
                row["root_ref_id"]: row["cnt"]
                for row in (
                    Masdar.objects.filter(root_ref_id__in=root_ids)
                    .values("root_ref_id")
                    .annotate(cnt=Count("id"))
                )
            }
            deriv_counts = {
                row["root_ref_id"]: row["cnt"]
                for row in (
                    Derivative.objects.filter(root_ref_id__in=root_ids)
                    .values("root_ref_id")
                    .annotate(cnt=Count("id"))
                )
            }
            for item in data["roots"]:
                rid = item["id"]
                item["masadir_count"] = masadir_counts.get(rid, 0)
                item["derivatives_count"] = deriv_counts.get(rid, 0)

    if type_filter in ("all", "masdar"):
        masadir = Masdar.objects.filter(
            Q(masdar_ar__icontains=q)
            | Q(masdar_plain__icontains=q)
            | Q(masdar_plain__icontains=nq)
            | Q(root_text__icontains=q)
        ).order_by("-is_attested", "-confidence")[:10]
        data["masadir"] = MasdarSerializer(masadir, many=True).data

    if type_filter in ("all", "derivative"):
        derivatives = Derivative.objects.filter(
            Q(form_ar__icontains=q)
            | Q(form_plain__icontains=nq)
            | Q(root_text__icontains=q)
        ).order_by("-is_quranic")[:10]
        data["derivatives"] = DerivativeSerializer(derivatives, many=True).data

    if type_filter in ("all", "word"):
        words = Word.objects.filter(
            Q(text__icontains=q)
            | Q(text_clean__icontains=q)
            | Q(text_clean__icontains=nq)
            | Q(translation__icontains=q)
        ).order_by("text")[:10]
        data["words"] = WordSerializer(words, many=True).data

        ayat = Ayah.objects.filter(text_uthmani__icontains=q)[:5]
        data["ayat"] = AyahSerializer(ayat, many=True).data

    return Response(data)


@api_view(["GET"])
def stats(request):
    tables = ["surahs", "ayat", "words", "roots", "masadir", "derivatives"]
    counts = {}
    with connection.cursor() as cur:
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
    return Response(
        {
            "surahs": counts["surahs"],
            "ayat": counts["ayat"],
            "words": counts["words"],
            "roots": counts["roots"],
            "masadir": counts["masadir"],
            "derivatives": counts["derivatives"],
            "word_occurrences": 77429,
        }
    )
