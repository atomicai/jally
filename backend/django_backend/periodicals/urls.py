from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MagazineViewSet, NewspaperViewSet

router = DefaultRouter()
router.register('magazine', MagazineViewSet, basename='magazine')
router.register('newspaper', NewspaperViewSet, basename='newspaper')


urlpatterns = [
    path("", include(router.urls)),
]
