from django.db import models


# Create your models here.
class Author(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class PublishingHouse(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    publishing_house = models.ForeignKey(PublishingHouse, on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    description = models.CharField(max_length=500)
    year = models.IntegerField()
    status = models.BooleanField()
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
