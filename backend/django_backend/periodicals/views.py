from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, permissions, viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import DjangoModelPermissions

import periodicals
from .serialisers import PeriodicalSerializer
from .models import PeriodicalsItem, PeriodicalsType, PublishingHouse
# from .filters import BookFilter
from user_app.permission import DjangoModelPermissionsStrict


class MagazineViewSet(viewsets.ModelViewSet):
    permissions_class = [DjangoModelPermissionsStrict]
    serializer_class = PeriodicalSerializer
    type = PeriodicalsType.objects.get(id=2)
    queryset = PeriodicalsItem.objects.filter(type=type).prefetch_related('publisher', 'type')

    # filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter,)
    # filter_class = BookFilter

    def perform_create(self, serializer):

        publisher = PublishingHouse.objects.get_or_create(name=self.request.data.get('publisher'))[0]

        serializer.save(type=PeriodicalsType.objects.get(id=2), publisher=publisher)

    # def get_queryset(self):
    #     return Book.objects.all().prefetch_related('author', 'publishing_house', 'genre')


class NewspaperViewSet(viewsets.ModelViewSet):
    permissions_class = [DjangoModelPermissionsStrict]
    serializer_class = PeriodicalSerializer
    type = PeriodicalsType.objects.get(id=1)
    queryset = PeriodicalsItem.objects.filter(type=type).prefetch_related('publisher', 'type')

    # filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter,)
    # filter_class = BookFilter

    def perform_create(self, serializer):

        publisher = PublishingHouse.objects.get_or_create(name=self.request.data.get('publisher'))[0]

        serializer.save(type=PeriodicalsType.objects.get(id=1), publisher=publisher)

    # def get_queryset(self):
    #     return Book.objects.all().prefetch_related('author', 'publishing_house', 'genre')
