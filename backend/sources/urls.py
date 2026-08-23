from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SourceViewSet

router = DefaultRouter()
router.register(r"sources", SourceViewSet, basename="source")

urlpatterns = [
    path("", include(router.urls)),
]
