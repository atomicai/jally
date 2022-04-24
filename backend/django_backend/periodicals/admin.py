from django.contrib import admin
from .models import PeriodicalsType, PeriodicalsItem


# Register your models here.
@admin.register(PeriodicalsType)
class PeriodicalsTypeAdmin(admin.ModelAdmin):
    # list_display = ['__all__']
    pass


@admin.register(PeriodicalsItem)
class PeriodicalsItemAdmin(admin.ModelAdmin):
    # list_display = ['__all__']
    pass
