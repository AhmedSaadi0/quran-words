from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AyahViewSet,
    AyahWordsViewSet,
    SurahViewSet,
    mushaf_page_detail,
    mushaf_pages,
)

router = DefaultRouter()
router.register(r"surahs", SurahViewSet, basename="surah")
router.register(r"ayat", AyahViewSet, basename="ayah")
router.register(r"ayah-words", AyahWordsViewSet, basename="ayah-words")

urlpatterns = [
    path("pages/", mushaf_pages, name="mushaf-pages"),
    path("pages/<int:page_number>/", mushaf_page_detail, name="mushaf-page-detail"),
    path("", include(router.urls)),
]
