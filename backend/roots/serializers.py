from rest_framework import serializers

from .models import Root, RootMeaning


class RootSerializer(serializers.ModelSerializer):
    meanings_count = serializers.SerializerMethodField()
    masadir_count = serializers.SerializerMethodField()
    derivatives_count = serializers.SerializerMethodField()

    class Meta:
        model = Root
        fields = ["id", "root", "meanings_count", "masadir_count", "derivatives_count"]

    def get_meanings_count(self, obj):
        return getattr(obj, "meanings_count", 0)

    def get_masadir_count(self, obj):
        return getattr(obj, "masadir_count", 0)

    def get_derivatives_count(self, obj):
        return getattr(obj, "derivatives_count", 0)


class RootMeaningSerializer(serializers.ModelSerializer):
    root_text = serializers.CharField(source="root.root", read_only=True)

    class Meta:
        model = RootMeaning
        fields = ["id", "root", "root_text", "definition", "book_name", "source_url"]
