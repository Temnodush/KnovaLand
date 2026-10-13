from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, SectionViewSet

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("sections", SectionViewSet, basename="section")

urlpatterns = [path("", include(router.urls))]
