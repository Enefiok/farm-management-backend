from rest_framework import serializers
from .models import Flock, ProductionRecord, FarmActivity

class FlockSerializer(serializers.ModelSerializer):
    # Read-only computed fields
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
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default='')

    class Meta:
        model = ProductionRecord
        fields = [
            'id', 'flock', 'item', 'quantity_collected', 'quantity_damaged', 
            'quantity_saleable', 'notes', 'event_date', 'classification', 
            'created_at', 'created_by_name'
        ]
        read_only_fields = ['quantity_saleable', 'created_at', 'created_by_name']

    def validate_flock(self, value):
        # Point 5: Validate flock belongs to the farm in URL
        farm_id = self.context.get('farm_id')
        if value and farm_id and value.farm_id != farm_id:
            raise serializers.ValidationError("This flock does not belong to the specified farm.")
        return value

    def validate_item(self, value):
        # Point 5: Validate item belongs to the farm (assuming items are farm-scoped)
        farm_id = self.context.get('farm_id')
        if value and farm_id and value.farm_id != farm_id:
            raise serializers.ValidationError("This item does not belong to the specified farm.")
        return value

    def validate(self, data):
        # Point 3: Validate damaged <= collected
        collected = data.get('quantity_collected', self.instance.quantity_collected if self.instance else 0)
        damaged = data.get('quantity_damaged', self.instance.quantity_damaged if self.instance else 0)
        
        if damaged > collected:
            raise serializers.ValidationError({"quantity_damaged": "Damaged eggs cannot exceed collected eggs."})
        
        # Point 3: Calculate saleable on server
        data['quantity_saleable'] = collected - damaged
        return data


class FarmActivitySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default='')

    class Meta:
        model = FarmActivity
        fields = [
            'id', 'flock', 'activity_type', 'item', 'quantity', 'notes', 
            'event_date', 'classification', 'created_at', 'created_by_name'
        ]
        read_only_fields = ['created_at', 'created_by_name']

    def validate_flock(self, value):
        farm_id = self.context.get('farm_id')
        if value and farm_id and value.farm_id != farm_id:
            raise serializers.ValidationError("This flock does not belong to the specified farm.")
        return value

    def validate_item(self, value):
        farm_id = self.context.get('farm_id')
        if value and farm_id and hasattr(value, 'farm_id') and value.farm_id != farm_id:
            raise serializers.ValidationError("This item does not belong to the specified farm.")
        return value

    def validate(self, data):
        # Point 4: MORTALITY must not exceed current_count
        if data.get('activity_type') == 'MORTALITY' and data.get('flock') and data.get('quantity'):
            current = data['flock'].current_count
            if data['quantity'] > current:
                raise serializers.ValidationError({
                    "quantity": f"Mortality quantity ({data['quantity']}) cannot exceed current flock count ({current})."
                })
        return data