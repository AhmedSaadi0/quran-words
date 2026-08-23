from django.db import models


class Lemma(models.Model):
    lemma_ar = models.TextField(unique=True, blank=True, null=True)
    lemma_bw = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "lemmas"

    def __str__(self):
        return self.lemma_ar or ""


class WordMorphology(models.Model):
    word_ayah = models.OneToOneField(
        "words.WordAyah", models.DO_NOTHING, primary_key=True, db_column="word_ayah_id"
    )
    pos = models.TextField(blank=True, null=True)
    form = models.TextField(blank=True, null=True)
    aspect = models.TextField(blank=True, null=True)
    mood = models.TextField(blank=True, null=True)
    voice = models.TextField(blank=True, null=True)
    person = models.TextField(blank=True, null=True)
    gender = models.TextField(blank=True, null=True)
    number = models.TextField(blank=True, null=True)
    grammatical_case = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    derivation = models.TextField(blank=True, null=True)
    special = models.TextField(blank=True, null=True)
    root = models.ForeignKey(
        "roots.Root", models.DO_NOTHING, blank=True, null=True, db_column="root_id"
    )
    lemma = models.ForeignKey(
        "morphology.Lemma",
        models.DO_NOTHING,
        blank=True,
        null=True,
        db_column="lemma_id",
    )
    segments = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "word_morphology"
