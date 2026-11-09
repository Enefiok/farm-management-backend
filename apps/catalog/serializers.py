from rest_framework import serializers
from django.utils import timezone
from .models import Unit, Item, UnitConversion, Party, StockMovement

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'name', 'abbreviation']

class UnitConversionSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    
    class Meta:
        model = UnitConversion
        fields = ['id', 'unit', 'unit_name', 'factor', 'is_base']

class ItemSerializer(serializers.ModelSerializer):
    base_unit_name = serializers.CharField(source='base_unit.name', read_only=True)
    conversions = UnitConversionSerializer(many=True, read_only=True)
    current_stock = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    # NEW: Optional initial stock field (write-only, used only when creating an item)
    initial_stock = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, write_only=True, default=0
    )

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'category', 'base_unit', 'base_unit_name', 
            'is_stock_tracked', 'is_active', 'current_stock', 'conversions', 
            'initial_stock', 'created_at'
        ]
        read_only_fields = ['created_at', 'current_stock']

    def validate_base_unit(self, value):
        """
        Prevent changing the base unit if the item has already been used in transactions.
        """
        instance = self.instance
        if instance and instance.base_unit != value:
            from apps.transactions.models import PurchaseLine, SaleLine
            from apps.operations.models import ProductionRecord, FarmActivity
            
            is_used = (
                PurchaseLine.objects.filter(item=instance).exists() or
                SaleLine.objects.filter(item=instance).exists() or
                ProductionRecord.objects.filter(item=instance).exists() or
                FarmActivity.objects.filter(item=instance).exists()
            )
            
            if is_used:
                raise serializers.ValidationError(
                    "Cannot change the Base Unit of an item that has already been used in transactions. "
                    "Create a new item instead."
                )
        return value

    def create(self, validated_data):
        # Pop the initial_stock out so it isn't passed to Item.objects.create()
        initial_stock = validated_data.pop('initial_stock', 0)
        
        # Create the item normally
        item = Item.objects.create(**validated_data)
        
        # If initial stock was provided and is greater than 0, create an opening stock movement
        if initial_stock and float(initial_stock) > 0:
            StockMovement.objects.create(
                farm_id=item.farm_id,
                item=item,
                direction='IN',
                quantity=float(initial_stock),
                source_type='OPENING',
                source_id=item.id,
                event_date=timezone.now().date(),
                created_by=self.context['request'].user if self.context.get('request') else None,
                notes=f"Initial stock when item was created"
            )
        
        return item

    def update(self, instance, validated_data):
        # Pop initial_stock if present (we don't allow changing it on update)
        validated_data.pop('initial_stock', None)
        return super().update(instance, validated_data)


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ['id', 'name', 'party_type', 'phone', 'email', 'created_at']
        read_only_fields = ['created_at']

class StockMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default='')

    class Meta:
        model = StockMovement
        fields = [
            'id', 'item', 'item_name', 'direction', 'quantity', 'source_type', 
            'source_id', 'event_date', 'notes', 'entry_timestamp', 'created_by_name'
        ]
        read_only_fields = ['entry_timestamp', 'created_by_name']