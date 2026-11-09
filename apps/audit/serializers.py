from rest_framework import serializers
from django.db import transaction
from .models import Adjustment

class AdjustmentSerializer(serializers.ModelSerializer):
    entry_timestamp = serializers.DateTimeField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True, default='')
    
    class Meta:
        model = Adjustment
        fields = [
            'id', 'farm', 'target_model', 'target_id', 'reason', 
            'notes', 'changes', 'entry_timestamp', 'created_by_name'
        ]
        read_only_fields = ['id', 'farm', 'entry_timestamp', 'created_by_name']

    def validate_changes(self, value):
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError("Changes must be a non-empty list of field updates.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        changes_data = validated_data.pop('changes')
        target_model_name = validated_data.get('target_model')
        target_id = validated_data.get('target_id')

        # Import models inside the method to avoid circular dependency errors
        from apps.operations.models import Flock, ProductionRecord, FarmActivity
        from apps.transactions.models import Purchase, Sale, Expense

        # Map the string from the frontend to the actual Django Model
        MODEL_MAP = {
            'Flock': Flock,
            'Purchase': Purchase,
            'Sale': Sale,
            'Expense': Expense,
            'Production': ProductionRecord,
            'FarmActivity': FarmActivity,  # <-- ADDED THIS
        }

        ModelClass = MODEL_MAP.get(target_model_name)
        if not ModelClass:
            raise serializers.ValidationError({"target_model": f"Adjustments for '{target_model_name}' are not supported yet."})

        # Get the farm_pk from the view context to ensure tenant isolation
        view = self.context.get('view')
        farm_pk = view.kwargs.get('farm_pk') if view else None

        try:
            # Fetch the actual record. We filter by farm_pk to ensure users can't adjust other farms' records.
            instance = ModelClass.objects.get(id=target_id, farm_id=farm_pk)
        except ModelClass.DoesNotExist:
            raise serializers.ValidationError({"target_id": "Target record not found or does not belong to this farm."})

        # 1. Apply the changes to the instance
        for change in changes_data:
            field = change.get('field')
            new_value = change.get('new_value')

            # Handle common UI-to-Database field name mismatches
            if target_model_name == 'Flock' and field == 'starting_count':
                field = 'initial_count'
            
            # Map Production UI names to DB fields
            if target_model_name == 'Production':
                if field == 'Saleable quantity':
                    field = 'quantity_saleable'
                elif field == 'Collected':
                    field = 'quantity_collected'
                elif field == 'Damaged':
                    field = 'quantity_damaged'

            # Map FarmActivity UI names to DB fields
            if target_model_name == 'FarmActivity':
                if field == 'Quantity':
                    field = 'quantity'
                elif field == 'Notes':
                    field = 'notes'
                elif field == 'Type' or field == 'Activity Type':
                    field = 'activity_type'

            if hasattr(instance, field):
                setattr(instance, field, new_value)

        # 2. Recalculate dependent fields (Business Logic)
        # Note: Flock.current_count and mortality_rate are @properties that calculate 
        # themselves automatically based on the activities. No manual update needed here!

        # 3. Save the updated target record
        instance.save()

        # 4. Create the Adjustment audit record
        validated_data['changes'] = changes_data
        return super().create(validated_data)