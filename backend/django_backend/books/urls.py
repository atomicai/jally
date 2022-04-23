from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BooksViewSet
router = DefaultRouter()
router.register('list', BooksViewSet, basename='list')

urlpatterns = [
    path("books/", include(router.urls)),
]
