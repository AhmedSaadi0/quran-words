from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WordAyahViewSet, WordViewSet, word_detail

router = DefaultRouter()
router.register(r"words", WordViewSet, basename="word")
router.register(r"word-ayah", WordAyahViewSet, basename="word-ayah")

urlpatterns = [
    path("words/<int:pk>/detail/", word_detail, name="word-detail"),
    path("", include(router.urls)),
]
