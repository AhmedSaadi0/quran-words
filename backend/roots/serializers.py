from rest_framework import serializers

from .models import Root, RootMeaning


class RootSerializer(serializers.ModelSerializer):
    meanings_count = serializers.SerializerMethodField()
    masadir_count = serializers.SerializerMethodField()
    derivatives_count = serializers.SerializerMethodField()
    gloss_ar = serializers.SerializerMethodField()
    gloss_en = serializers.SerializerMethodField()
    gloss_source = serializers.SerializerMethodField()
    ai_summary_ar = serializers.SerializerMethodField()
    ai_summary_model = serializers.SerializerMethodField()
    ai_summary_generated_at = serializers.SerializerMethodField()

    class Meta:
        model = Root
        fields = [
            "id",
            "root",
            "meanings_count",
            "masadir_count",
            "derivatives_count",
            "gloss_ar",
            "gloss_en",
            "gloss_source",
            "ai_summary_ar",
            "ai_summary_model",
            "ai_summary_generated_at",
        ]

    def get_meanings_count(self, obj):
        return getattr(obj, "meanings_count", 0)

    def get_masadir_count(self, obj):
        return getattr(obj, "masadir_count", 0)

    def get_derivatives_count(self, obj):
        return getattr(obj, "derivatives_count", 0)

    def get_gloss_ar(self, obj):
        g = getattr(obj, "_gloss", None)
        return g.gloss_ar if g else None

    def get_gloss_en(self, obj):
        g = getattr(obj, "_gloss", None)
        return g.gloss_en if g else None

    def get_gloss_source(self, obj):
        g = getattr(obj, "_gloss", None)
        return g.ar_source if g else None

    def get_ai_summary_ar(self, obj):
        s = getattr(obj, "_ai_summary", None)
        return s.summary_ar if s else None

    def get_ai_summary_model(self, obj):
        s = getattr(obj, "_ai_summary", None)
        return s.model if s else None

    def get_ai_summary_generated_at(self, obj):
        s = getattr(obj, "_ai_summary", None)
        return s.generated_at if s else None


class RootMeaningSerializer(serializers.ModelSerializer):
    root_text = serializers.CharField(source="root.root", read_only=True)

    class Meta:
        model = RootMeaning
        fields = ["id", "root", "root_text", "definition", "book_name", "source_url"]
