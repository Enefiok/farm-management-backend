from rest_framework import serializers
from .models import Unit, Item, UnitConversion, Party

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name', 'abbreviation']

class UnitConversionSerializer(serializers.ModelSerializer):
    # Read-only field to show the unit name in the response
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    
    class Meta:
        model = UnitConversion
        fields = ['id', 'unit', 'unit_name', 'factor', 'is_base']

class ItemSerializer(serializers.ModelSerializer):
    base_unit_name = serializers.CharField(source='base_unit.name', read_only=True)
    # Nested read-only list of conversions for this item
    conversions = UnitConversionSerializer(many=True, read_only=True)

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'category', 'base_unit', 'base_unit_name', 
            'is_stock_tracked', 'conversions', 'created_at'
        ]
        read_only_fields = ['created_at']

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ['id', 'name', 'party_type', 'phone', 'email', 'created_at']
        read_only_fields = ['created_at']