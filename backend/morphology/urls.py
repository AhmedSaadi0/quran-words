from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LemmaViewSet, WordMorphologyViewSet

router = DefaultRouter()
router.register(r"lemmas", LemmaViewSet, basename="lemma")
router.register(r"morphology", WordMorphologyViewSet, basename="morphology")

urlpatterns = [
    path("", include(router.urls)),
]
