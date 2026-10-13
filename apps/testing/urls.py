from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TestViewSet

router = DefaultRouter()
router.register("tests", TestViewSet, basename="test")

urlpatterns = [path("", include(router.urls))]
