from rest_framework import serializers

from .models import Derivative, Masdar


class MasdarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Masdar
        fields = [
            "id",
            "root_ref",
            "root_text",
            "form",
            "lemma",
            "masdar_ar",
            "masdar_plain",
            "pattern",
            "is_attested",
            "source",
            "confidence",
        ]


class DerivativeSerializer(serializers.ModelSerializer):
    example_word_text = serializers.CharField(
        source="example_word.text", read_only=True, default=None
    )

    class Meta:
        model = Derivative
        fields = [
            "id",
            "root_ref",
            "root_text",
            "pattern",
            "derivative_type",
            "form_ar",
            "form_plain",
            "pos",
            "is_quranic",
            "camel_valid",
            "example_word",
            "example_word_text",
            "source",
        ]
