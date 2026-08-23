from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RootMeaningViewSet, RootViewSet

router = DefaultRouter()
router.register(r"roots", RootViewSet, basename="root")
router.register(r"meanings", RootMeaningViewSet, basename="meaning")

urlpatterns = [
    path("", include(router.urls)),
]
