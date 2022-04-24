from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, ProfileView,UsersListView
router = DefaultRouter()
router.register('list', UsersListView, basename='list')

urlpatterns = [
    path("reg/", RegisterView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("users/", include(router.urls)),
]
