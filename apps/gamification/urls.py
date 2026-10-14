from django.urls import path

from .views import (
    AchievementListView,
    CompleteMaterialView,
    EnrollView,
    LeaderboardView,
    MyEnrollmentsView,
    MyProfileView,
    PurchaseView,
)

urlpatterns = [
    path("game/profile/", MyProfileView.as_view(), name="game-profile"),
    path("game/leaderboard/", LeaderboardView.as_view(), name="game-leaderboard"),
    path("game/achievements/", AchievementListView.as_view(), name="game-achievements"),
    path("game/enrollments/", MyEnrollmentsView.as_view(), name="game-enrollments"),
    path("game/enroll/", EnrollView.as_view(), name="game-enroll"),
    path("game/purchase/", PurchaseView.as_view(), name="game-purchase"),
    path("game/progress/", CompleteMaterialView.as_view(), name="game-progress"),
]
