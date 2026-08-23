from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from morphology.serializers import WordMorphologySerializer

from .models import Word, WordAyah


class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = [
            "id",
            "text",
            "text_clean",
            "translation",
            "transliteration",
            "position_in_ayah",
        ]


class WordAyahSerializer(serializers.ModelSerializer):
    word = WordSerializer(read_only=True)
    ayah = serializers.SerializerMethodField()
    morphology = serializers.SerializerMethodField()

    class Meta:
        model = WordAyah
        fields = ["id", "word", "ayah", "position", "location", "morphology"]

    def get_ayah(self, obj):
        # Imported lazily to avoid a circular import with quran.serializers
        from quran.serializers import AyahSerializer

        return AyahSerializer(obj.ayah).data

    def get_morphology(self, obj):
        try:
            wm = obj.wordmorphology
        except ObjectDoesNotExist:
            return None
        return WordMorphologySerializer(wm).data
