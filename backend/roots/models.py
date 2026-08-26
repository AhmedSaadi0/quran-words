from django.db import models


class Root(models.Model):
    root = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = "roots"

    def __str__(self):
        return self.root


class RootMeaning(models.Model):
    root = models.ForeignKey("roots.Root", models.DO_NOTHING, db_column="root_id")
    definition = models.TextField(blank=True, null=True)
    book_name = models.TextField(blank=True, null=True)
    source_url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "root_meanings"


class RootGloss(models.Model):
    """المعنى السريع المختصر للجذر (سطر/سطران) — يبنى بـ scripts/build_root_glosses.py"""

    root_id = models.OneToOneField(
        "roots.Root",
        models.DO_NOTHING,
        primary_key=True,
        db_column="root_id",
        related_name="gloss",
    )
    gloss_ar = models.TextField(blank=True, null=True)
    gloss_en = models.TextField(blank=True, null=True)
    ar_source = models.TextField(blank=True, null=True)
    en_source = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "root_glosses"


class RootAiSummary(models.Model):
    """الملخص المولد بالذكاء الاصطناعي للمعنى العام للجذر — يبنى بـ scripts/build_root_ai_summary.py"""

    root_id = models.OneToOneField(
        "roots.Root",
        models.DO_NOTHING,
        primary_key=True,
        db_column="root_id",
        related_name="ai_summary",
    )
    summary_ar = models.TextField(blank=True, null=True)
    model = models.TextField(blank=True, null=True)
    generated_at = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "root_ai_summary"
