from rest_framework import serializers
from .models import Flock, ProductionRecord, FarmActivity

class FlockSerializer(serializers.ModelSerializer):
    # Flock does NOT inherit from BaseModel, it has created_at
    current_count = serializers.IntegerField(read_only=True)
    mortality_rate = serializers.FloatField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default='')

    class Meta:
        model = Flock
        fields = [
            'id', 'identifier', 'breed', 'arrival_date', 'age_at_arrival', 
            'initial_count', 'current_count', 'mortality_rate', 
            'stage', 'status', 'created_at', 'created_by_name'
        ]
        read_only_fields = ['created_at', 'current_count', 'mortality_rate', 'created_by_name']


class ProductionRecordSerializer(serializers.ModelSerializer):
    # ProductionRecord inherits from BaseModel, which uses entry_timestamp
    entry_timestamp = serializers.DateTimeField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default='')

    # NEW: Accept separate units for collected and damaged
    unit_collected = serializers.CharField(write_only=True, required=False, default='Egg')
    unit_damaged = serializers.CharField(write_only=True, required=False, default='Egg')

    class Meta:
        model = ProductionRecord
        fields = [
            'id', 'flock', 'item', 'quantity_collected', 'quantity_damaged', 
            'quantity_saleable', 'unit', 'notes', 'event_date', 'classification', 
            'entry_timestamp', 'created_by_name', 'unit_collected', 'unit_damaged'
        ]
        read_only_fields = ['quantity_saleable', 'entry_timestamp', 'created_by_name']

    def _get_farm_pk(self):
        view = self.context.get('view')
        return view.kwargs.get('farm_pk') if view else None

    def validate_flock(self, value):
        farm_pk = self._get_farm_pk()
        if value and farm_pk and value.farm_id != farm_pk:
            raise serializers.ValidationError("This flock does not belong to the specified farm.")
        return value

    def validate_item(self, value):
        farm_pk = self._get_farm_pk()
        if value and farm_pk and value.farm_id != farm_pk:
            raise serializers.ValidationError("This item does not belong to the specified farm.")
        return value

    def validate(self, data):
        # We need the item to find conversions
        item = data.get('item', self.instance.item if self.instance else None)
        if not item:
            return data

        # Get units from input (default to 'Egg' if not provided)
        unit_collected_str = data.get('unit_collected', 'Egg')
        unit_damaged_str = data.get('unit_damaged', 'Egg')
        
        collected_raw = data.get('quantity_collected', 0)
        damaged_raw = data.get('quantity_damaged', 0)

        # Helper to convert to base unit
        def to_base(qty, unit_name):
            if not unit_name or unit_name == item.base_unit.name:
                return qty
            try:
                from apps.catalog.models import Unit, UnitConversion
                unit_obj = Unit.objects.filter(name__iexact=unit_name).first()
                if unit_obj:
                    conv = UnitConversion.objects.get(item=item, unit=unit_obj)
                    return qty * conv.factor
            except Exception:
                pass
            return qty

        # Convert to base units (e.g., Eggs)
        base_collected = to_base(collected_raw, unit_collected_str)
        base_damaged = to_base(damaged_raw, unit_damaged_str)

        if base_damaged > base_collected:
            raise serializers.ValidationError({"quantity_damaged": "Damaged amount cannot exceed collected amount."})

        # Save the calculated base values into the actual model fields
        data['quantity_collected'] = base_collected
        data['quantity_damaged'] = base_damaged
        data['quantity_saleable'] = base_collected - base_damaged
        data['unit'] = item.base_unit.name # Store as base unit name (e.g., "Egg")
        
        # Remove the write-only fields so they don't crash the save
        data.pop('unit_collected', None)
        data.pop('unit_damaged', None)

        return data

    def create(self, validated_data):
        # AUTO-DETECT EGG ITEM: If the frontend didn't send an item ID, find the active EGG item for this farm
        if not validated_data.get('item'):
            from apps.catalog.models import Item
            egg_item = Item.objects.filter(
                farm_id=validated_data.get('farm_id'),
                category='EGG',
                is_active=True
            ).first()
            if egg_item:
                validated_data['item'] = egg_item
        
        # 1. Create the production record normally
        record = ProductionRecord.objects.create(**validated_data)
        
        # 2. STOCK LEDGER INTEGRATION: Add eggs to stock (IN)
        if record.item and record.item.is_stock_tracked:
            from apps.catalog.models import StockMovement
            
            StockMovement.objects.create(
                farm_id=record.farm_id,
                item=record.item,
                direction='IN',
                quantity=record.quantity_saleable,
                source_type='PRODUCTION',
                source_id=record.id,
                event_date=record.event_date,
                created_by=record.created_by,
                notes=f"Egg production recorded: {record.quantity_saleable} {record.unit}"
            )
            
        return record


class FarmActivitySerializer(serializers.ModelSerializer):
    # FarmActivity inherits from BaseModel, which uses entry_timestamp
    entry_timestamp = serializers.DateTimeField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default='')

    class Meta:
        model = FarmActivity
        fields = [
            'id', 'flock', 'activity_type', 'item', 'quantity', 'notes', 
            'event_date', 'classification', 'entry_timestamp', 'created_by_name'
        ]
        read_only_fields = ['entry_timestamp', 'created_by_name']

    def _get_farm_pk(self):
        view = self.context.get('view')
        return view.kwargs.get('farm_pk') if view else None

    def validate_flock(self, value):
        farm_pk = self._get_farm_pk()
        if value and farm_pk and value.farm_id != farm_pk:
            raise serializers.ValidationError("This flock does not belong to the specified farm.")
        return value

    def validate_item(self, value):
        farm_pk = self._get_farm_pk()
        if value and farm_pk and hasattr(value, 'farm_id') and value.farm_id != farm_pk:
            raise serializers.ValidationError("This item does not belong to the specified farm.")
        return value

    def validate(self, data):
        if data.get('activity_type') == 'MORTALITY' and data.get('flock') and data.get('quantity'):
            current = data['flock'].current_count
            if data['quantity'] > current:
                raise serializers.ValidationError({
                    "quantity": f"Mortality quantity ({data['quantity']}) cannot exceed current flock count ({current})."
                })
        return data

    def create(self, validated_data):
        # 1. Create the activity record normally
        record = FarmActivity.objects.create(**validated_data)
        
        # 2. STOCK LEDGER INTEGRATION: Subtract feed/medicine from stock (OUT)
        # This only runs if the activity is Feed/Medication AND an item is linked
        if record.item and record.item.is_stock_tracked and record.activity_type in ['FEED_CONSUMPTION', 'MEDICATION']:
            from apps.catalog.models import StockMovement
            
            StockMovement.objects.create(
                farm_id=record.farm_id,
                item=record.item,
                direction='OUT',
                quantity=record.quantity,
                source_type='ACTIVITY',
                source_id=record.id,
                event_date=record.event_date,
                created_by=record.created_by,
                notes=f"Farm activity: {record.get_activity_type_display()}"
            )
            
        return record