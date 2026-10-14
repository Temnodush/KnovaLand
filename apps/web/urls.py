from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("courses/<int:pk>/", views.course_detail, name="course-detail"),
    path("courses/<int:pk>/enroll/", views.enroll_course, name="enroll"),
    path("courses/<int:pk>/buy/", views.buy_course, name="buy"),
    path("lessons/<int:pk>/", views.lesson_detail, name="lesson-detail"),
    path("lessons/<int:pk>/trainer/", views.trainer, name="trainer"),
    path("lessons/<int:pk>/trainer/submit/", views.trainer_submit, name="trainer-submit"),
    path("materials/<int:pk>/complete/", views.complete_material, name="complete-material"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("profile/", views.profile_view, name="profile"),
    # Регистрация и подтверждение email
    path("register/", views.register, name="register"),
    path("verify-email/resend/", views.resend_verification, name="resend-verification"),
    path("verify-email/<str:token>/", views.verify_email, name="verify-email"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
