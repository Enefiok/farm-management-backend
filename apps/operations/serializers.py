from rest_framework import serializers
from .models import Flock, ProductionRecord, FarmActivity

class FlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flock
        fields = ['id', 'identifier', 'breed', 'arrival_date', 'initial_count', 'created_at']
        read_only_fields = ['created_at']

class ProductionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionRecord
        fields = ['id', 'flock', 'item', 'quantity_collected', 'quantity_damaged', 'quantity_saleable', 'event_date', 'classification']
        # Note: entry_timestamp and created_by are handled automatically by BaseModel

class FarmActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmActivity
        fields = ['id', 'flock', 'activity_type', 'item', 'quantity', 'notes', 'event_date', 'classification']