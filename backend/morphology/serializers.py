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
    root_gloss = serializers.SerializerMethodField()

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
            "root_gloss",
            "lemma",
            "lemma_text",
            "segments",
        ]

    def get_root_gloss(self, obj):
        """المعنى السريع للجذر — يُمرر عبر context من AyahWordsViewSet."""
        gloss_map = self.context.get("root_glosses") or {}
        g = gloss_map.get(obj.root_id)
        return g.gloss_ar if g else None
