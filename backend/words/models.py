from django.db import models


class Word(models.Model):
    text = models.TextField()
    text_clean = models.TextField(blank=True, null=True)
    text_plain = models.TextField(
        blank=True,
        null=True,
        help_text="نص مطبّع للبحث — يُبنى بـ scripts/build_plain_columns.py",
    )
    translation = models.TextField(blank=True, null=True)
    transliteration = models.TextField(blank=True, null=True)
    position_in_ayah = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "words"

    def __str__(self):
        return self.text


class WordAyah(models.Model):
    word = models.ForeignKey("words.Word", models.DO_NOTHING)
    ayah = models.ForeignKey("quran.Ayah", models.DO_NOTHING)
    position = models.IntegerField()
    location = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "word_ayah"

    def __str__(self):
        return self.location or f"{self.ayah_id}:{self.position}"
