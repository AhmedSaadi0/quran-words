from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AyahViewSet, AyahWordsViewSet, SurahViewSet

router = DefaultRouter()
router.register(r"surahs", SurahViewSet, basename="surah")
router.register(r"ayat", AyahViewSet, basename="ayah")
router.register(r"ayah-words", AyahWordsViewSet, basename="ayah-words")

urlpatterns = [
    path("", include(router.urls)),
]
