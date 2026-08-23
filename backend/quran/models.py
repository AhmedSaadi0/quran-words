from django.db import models


class Surah(models.Model):
    name_ar = models.TextField()
    name_en = models.TextField()
    ayah_count = models.IntegerField()
    revelation_type = models.TextField()
    juz_start = models.IntegerField()

    class Meta:
        managed = False
        db_table = "surahs"

    def __str__(self):
        return f"{self.id} - {self.name_ar}"


class Ayah(models.Model):
    surah = models.ForeignKey(Surah, models.DO_NOTHING, db_column="surah")
    ayah = models.IntegerField()
    text_uthmani = models.TextField(blank=True, null=True)
    text_uthmani_plain = models.TextField(
        blank=True,
        null=True,
        help_text="نص عثماني مطبّع — يُبنى بـ scripts/build_plain_columns.py",
    )
    text_imlaei = models.TextField(blank=True, null=True)
    word_count = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ayat"
        unique_together = (("surah", "ayah"),)

    def __str__(self):
        return f"{self.surah_id}:{self.ayah}"
