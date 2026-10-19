from rest_framework import serializers
from .models import Item, Party

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'category', 'base_unit', 'is_stock_tracked', 'created_at']
        read_only_fields = ['created_at']

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ['id', 'name', 'party_type', 'phone', 'email', 'created_at']
        read_only_fields = ['created_at']