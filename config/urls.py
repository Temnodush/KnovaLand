from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API
    path("api/auth/", include("apps.users.urls_auth")),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.courses.urls")),
    path("api/", include("apps.materials.urls")),
    path("api/", include("apps.testing.urls")),
    # Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
