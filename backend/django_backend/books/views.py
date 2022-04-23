from django.shortcuts import render

from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import DjangoModelPermissions
from .serialisers import BookSerializer
from .models import Book, Author, PublishingHouse, Genre
from user_app.permission import DjangoModelPermissionsStrict


class BooksViewSet(viewsets.ModelViewSet):
    permissions_class = [DjangoModelPermissionsStrict]
    serializer_class = BookSerializer
    queryset = Book.objects.all().prefetch_related('author', 'publishing_house', 'genre')

    def perform_create(self, serializer):

        author = Author.objects.get_or_create(name=self.request.data.get('author'))[0]
        genre = Genre.objects.get_or_create(name=self.request.data.get('genre'))[0]
        publishing_house = PublishingHouse.objects.get_or_create(name=self.request.data.get('publishing_house'))[0]

        serializer.save(genre=genre, author=author, publishing_house=publishing_house)
