from rest_framework import serializers
from .models import Book, Author, PublishingHouse


class BookSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(many=False)
    publishing_house = serializers.StringRelatedField(many=False)
    genre = serializers.StringRelatedField(many=False)

    class Meta:
        model = Book
        fields = '__all__'
        lookup_fields = 'pk'

    def create(self, validated_data):
        book = Book.objects.create(**validated_data)
        return book

