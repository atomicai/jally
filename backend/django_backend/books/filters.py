import django_filters

from .models import Book


class BookFilter(django_filters.rest_framework.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    author = django_filters.CharFilter(field_name='author__name', lookup_expr='icontains')
    publishing_house = django_filters.CharFilter(field_name='publishing_house__name', lookup_expr='icontains')
    genre = django_filters.CharFilter(field_name='genre__name', lookup_expr='icontains')
    year = django_filters.CharFilter(lookup_expr='iexact')
    year_lt = django_filters.CharFilter(field_name='year', lookup_expr='lt')
    year_gt = django_filters.CharFilter(field_name='year', lookup_expr='gt')

    class Meta:
        model = Book

        # fields = {
        #     'title': ['icontains',],
        #     'author': ['icontains',],
        #     'year': ['iexact', 'gt', 'lt'],
        # }

        fields = ['title', 'author', 'publishing_house', 'genre', 'year', 'year_lt', 'year_gt']
