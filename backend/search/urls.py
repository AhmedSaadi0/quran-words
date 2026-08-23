from django.urls import path

from .views import stats, unified_search

urlpatterns = [
    path("search/", unified_search, name="unified-search"),
    path("stats/", stats, name="stats"),
]
