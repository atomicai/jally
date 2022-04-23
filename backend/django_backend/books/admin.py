from django.contrib import admin

from .models import Author, PublishingHouse, Book, Genre


# Register your models here.
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    pass


@admin.register(PublishingHouse)
class PublishingHouseAdmin(admin.ModelAdmin):
    pass


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    pass


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass
