from rest_framework import serializers

from .models import Lemma, WordMorphology


class LemmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lemma
        fields = ["id", "lemma_ar", "lemma_bw"]


class WordMorphologySerializer(serializers.ModelSerializer):
    root_text = serializers.CharField(source="root.root", read_only=True, default=None)
    lemma_text = serializers.CharField(
        source="lemma.lemma_ar", read_only=True, default=None
    )

    class Meta:
        model = WordMorphology
        fields = [
            "word_ayah",
            "pos",
            "form",
            "aspect",
            "mood",
            "voice",
            "person",
            "gender",
            "number",
            "grammatical_case",
            "state",
            "derivation",
            "special",
            "root",
            "root_text",
            "lemma",
            "lemma_text",
            "segments",
        ]
