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
    # Quran divisions — from Quran.com API v4 (CC-BY-4.0)
    # Filled by scripts/enrich_ayat_quran_meta.py
    juz = models.IntegerField(
        blank=True, null=True, db_index=True, help_text="1..30 — juz_number"
    )
    hizb = models.IntegerField(
        blank=True, null=True, db_index=True, help_text="1..60 — hizb_number"
    )
    rub_el_hizb = models.IntegerField(
        blank=True,
        null=True,
        db_index=True,
        db_column="rub_el_hizb",
        help_text="1..240 — rub_el_hizb_number (quarter)",
    )
    page_number = models.IntegerField(
        blank=True, null=True, db_index=True, help_text="1..604 — Madina page"
    )
    manzil_number = models.IntegerField(
        blank=True, null=True, help_text="1..7 — manzil"
    )
    ruku_number = models.IntegerField(blank=True, null=True, help_text="1..558 — ruku")
    sajdah_number = models.IntegerField(
        blank=True, null=True, help_text="sajdah id if ayat is sajdah"
    )

    class Meta:
        managed = False
        db_table = "ayat"
        unique_together = (("surah", "ayah"),)

    def __str__(self):
        return f"{self.surah_id}:{self.ayah}"
