from rest_framework import serializers

from morphology.models import WordMorphology
from morphology.serializers import WordMorphologySerializer
from words.serializers import WordSerializer

from .models import Ayah, Surah


class SurahSerializer(serializers.ModelSerializer):
    class Meta:
        model = Surah
        fields = [
            "id",
            "name_ar",
            "name_en",
            "ayah_count",
            "revelation_type",
            "juz_start",
        ]


class AyahSerializer(serializers.ModelSerializer):
    surah_name = serializers.CharField(source="surah.name_ar", read_only=True)

    class Meta:
        model = Ayah
        fields = [
            "id",
            "surah",
            "surah_name",
            "ayah",
            "text_uthmani",
            "text_imlaei",
            "word_count",
        ]


class AyahWithWordsSerializer(serializers.ModelSerializer):
    surah_name = serializers.CharField(source="surah.name_ar", read_only=True)
    surah_name_en = serializers.CharField(source="surah.name_en", read_only=True)
    words = serializers.SerializerMethodField()

    class Meta:
        model = Ayah
        fields = [
            "id",
            "surah",
            "surah_name",
            "surah_name_en",
            "ayah",
            "text_uthmani",
            "word_count",
            "words",
        ]

    def get_words(self, obj):
        # Prefetched wordayah set (to_attr="prefetched_wordayah")
        wordayahs = getattr(obj, "prefetched_wordayah", None)
        if wordayahs is None:
            wordayahs = obj.wordayah_set.select_related(
                "word",
                "wordmorphology",
                "wordmorphology__root",
                "wordmorphology__lemma",
            ).order_by("position")
        result = []
        for wa in wordayahs:
            wm = None
            try:
                wm = wa.wordmorphology
            except WordMorphology.DoesNotExist:
                pass
            morph = WordMorphologySerializer(wm).data if wm else None
            result.append(
                {
                    "word_ayah_id": wa.id,
                    "position": wa.position,
                    "location": wa.location,
                    "word": WordSerializer(wa.word).data,
                    "morphology": morph,
                }
            )
        return result
