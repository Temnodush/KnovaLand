from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from .views import LoginView, RefreshView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", LoginView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
]
