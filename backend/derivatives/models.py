from django.db import models


class Masdar(models.Model):
    root_ref = models.ForeignKey("roots.Root", models.DO_NOTHING, db_column="root_id")
    root_text = models.TextField(db_column="root")
    form = models.TextField(blank=True, null=True)
    lemma = models.ForeignKey(
        "morphology.Lemma",
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_column="lemma_id",
    )
    masdar_ar = models.TextField()
    masdar_plain = models.TextField()
    pattern = models.TextField(blank=True, null=True)
    is_attested = models.BooleanField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "masadir"

    def __str__(self):
        return f"{self.root_text} -> {self.masdar_ar}"


class Derivative(models.Model):
    root_ref = models.ForeignKey("roots.Root", models.DO_NOTHING, db_column="root_id")
    root_text = models.TextField(db_column="root")
    pattern = models.TextField()
    derivative_type = models.TextField()
    form_ar = models.TextField()
    form_plain = models.TextField()
    pos = models.TextField(blank=True, null=True)
    is_quranic = models.BooleanField(blank=True, null=True)
    camel_valid = models.BooleanField(blank=True, null=True)
    example_word = models.ForeignKey(
        "words.Word",
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_column="example_word_id",
    )
    source = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "derivatives"


class WordMasdar(models.Model):
    word_ayah = models.ForeignKey(
        "words.WordAyah", models.DO_NOTHING, db_column="word_ayah_id"
    )
    masdar = models.ForeignKey(
        "derivatives.Masdar", models.DO_NOTHING, db_column="masdar_id"
    )

    class Meta:
        managed = False
        db_table = "word_masdar"
        unique_together = (("word_ayah", "masdar"),)
