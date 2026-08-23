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
