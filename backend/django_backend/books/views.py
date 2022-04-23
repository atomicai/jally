from django.shortcuts import render

from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import DjangoModelPermissions
from .serialisers import BookSerializer
from .models import Book


class BooksViewSet(viewsets.ModelViewSet):
    permissions_class = [DjangoModelPermissions]
    serializer_class = BookSerializer
    queryset = Book.objects.all().prefetch_related('author', 'publishing_house')
