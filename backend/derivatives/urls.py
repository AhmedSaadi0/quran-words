from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DerivativeViewSet, MasdarViewSet

router = DefaultRouter()
router.register(r"masadir", MasdarViewSet, basename="masdar")
router.register(r"derivatives", DerivativeViewSet, basename="derivative")

urlpatterns = [
    path("", include(router.urls)),
]
