from django.db import models

# Create your models here.


from books.models import PublishingHouse


class PeriodicalsType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PeriodicalsItem(models.Model):
    title = models.CharField(max_length=200)
    publish_number = models.IntegerField()
    date = models.DateField()
    publisher = models.ForeignKey(PublishingHouse, on_delete=models.CASCADE)
    type = models.ForeignKey(PeriodicalsType, on_delete=models.CASCADE)
    status = models.BooleanField()

    def __str__(self):
        return self.title

