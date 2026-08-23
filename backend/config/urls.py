from django.contrib import admin
from django.urls import include, path

api_patterns = [
    path("", include("quran.urls")),
    path("", include("words.urls")),
    path("", include("morphology.urls")),
    path("", include("roots.urls")),
    path("", include("derivatives.urls")),
    path("", include("sources.urls")),
    path("", include("search.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
]
