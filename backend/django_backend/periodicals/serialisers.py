from rest_framework import serializers
from .models import PeriodicalsItem, PeriodicalsType


class PeriodicalSerializer(serializers.ModelSerializer):
    publisher = serializers.StringRelatedField(many=False)
    type = serializers.StringRelatedField(many=False)

    class Meta:
        model = PeriodicalsItem
        fields = '__all__'
        lookup_fields = 'pk'

    def create(self, validated_data):
        book = PeriodicalsType.objects.create(**validated_data)
        return book
