from django.db import models


class Source(models.Model):
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "sources"


class WordSource(models.Model):
    word = models.ForeignKey("words.Word", models.DO_NOTHING)
    source = models.ForeignKey("sources.Source", models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "word_sources"
