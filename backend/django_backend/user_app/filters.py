import django_filters

from django.contrib.auth.models import Group, User


class UserGroupFilter(django_filters.rest_framework.FilterSet):

    group = django_filters.CharFilter(field_name='group__name', lookup_expr='iexact')

    class Meta:
        model = User
        fields = ['group', ]
