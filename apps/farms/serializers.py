from rest_framework import serializers
from django.db import transaction
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .models import Farm, OpeningPosition, OpeningFlockLine, OpeningStockLine
from apps.operations.models import Flock

class CreateFarmSerializer(serializers.ModelSerializer):
    # Farm settings fields (allow_blank=True prevents crashes on empty strings)
    currency = serializers.CharField(max_length=3, required=False, default='NGN', allow_blank=True)
    timezone = serializers.CharField(max_length=50, required=False, default='Africa/Lagos', allow_blank=True)
    unit_system = serializers.CharField(max_length=10, required=False, default='metric', allow_blank=True)
    
    # NEW FIELD: Expose farm_type to the API
    farm_type = serializers.ChoiceField(
        choices=Farm.FarmTypeChoices.choices, 
        required=False, 
        default=Farm.FarmTypeChoices.LAYERS
    )
    
    class Meta:
        model = Farm
        # Added 'farm_type' to the fields list
        fields = ['name', 'location', 'contact_info', 'currency', 'timezone', 'unit_system', 'farm_type']
    
    def validate_currency(self, value):
        if not value or not value.strip():
            return 'NGN'
        value = value.upper().strip()
        supported_currencies = [
            'NGN', 'USD', 'EUR', 'GBP', 'GHS', 'KES', 'ZAR', 
            'XOF', 'XAF', 'CAD', 'AUD', 'JPY', 'CNY', 'INR', 'BRL'
        ]
        if value not in supported_currencies:
            raise serializers.ValidationError(
                f"Currency '{value}' is not supported. Choose from: {', '.join(supported_currencies)}"
            )
        return value
    
    def validate_timezone(self, value):
        if not value or not value.strip():
            return 'Africa/Lagos'
        try:
            ZoneInfo(value.strip())
        except (ZoneInfoNotFoundError, KeyError):
            raise serializers.ValidationError(
                f"Timezone '{value}' is not valid. Use IANA timezone names (e.g., Africa/Lagos, America/New_York)"
            )
        return value
    
    def validate_unit_system(self, value):
        if not value or not value.strip():
            return 'metric'
        value = value.lower().strip()
        allowed_choices = ['metric', 'imperial']
        if value not in allowed_choices:
            raise serializers.ValidationError(
                f"Unit system '{value}' is not allowed. Choose from: {', '.join(allowed_choices)}"
            )
        return value


# --- SPRINT 3 SERIALIZERS: OPENING POSITION ---

class OpeningFlockLineSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=50)
    initial_count = serializers.IntegerField(min_value=1)
    breed = serializers.CharField(max_length=100, required=False, allow_blank=True)
    stage = serializers.CharField(max_length=20, required=False, allow_blank=True)
    arrival_date = serializers.DateField(required=False) # <-- ADDED: Individual arrival date for each flock

class OpeningStockLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpeningStockLine
        fields = ['item', 'quantity']

class OpeningPositionSerializer(serializers.ModelSerializer):
    flock_lines = OpeningFlockLineSerializer(many=True, required=False)
    stock_lines = OpeningStockLineSerializer(many=True, required=False)

    class Meta:
        model = OpeningPosition
        fields = ['id', 'farm', 'event_date', 'classification', 'status', 'flock_lines', 'stock_lines', 'entry_timestamp', 'created_by']
        read_only_fields = ['id', 'farm', 'entry_timestamp', 'created_by']
        extra_kwargs = {
            'classification': {'read_only': True, 'default': 'OPENING'}
        }

    def validate_flock_lines(self, value):
        # Safely get farm_pk from the URL kwargs
        view = self.context.get('view')
        farm_pk = view.kwargs.get('farm_pk') if view else None
        if not farm_pk:
            raise serializers.ValidationError("Farm ID is required.")
        
        farm = Farm.objects.get(pk=farm_pk)
        identifiers = [line['identifier'] for line in value]
        
        # Check against existing real Flocks in the database
        if Flock.objects.filter(farm=farm, identifier__in=identifiers).exists():
            raise serializers.ValidationError("One or more flock identifiers already exist on this farm.")
        
        # Check against other lines in the same request payload
        if len(identifiers) != len(set(identifiers)):
            raise serializers.ValidationError("Duplicate flock identifiers found in this request.")
            
        return value

    @transaction.atomic
    def create(self, validated_data):
        flock_lines_data = validated_data.pop('flock_lines', [])
        stock_lines_data = validated_data.pop('stock_lines', [])
        
        # Safely get the farm from the view kwargs
        view = self.context.get('view')
        farm_pk = view.kwargs.get('farm_pk') if view else None
        farm = Farm.objects.get(pk=farm_pk)
        
        # 1. Create the main Opening Position snapshot
        position = OpeningPosition.objects.create(farm=farm, **validated_data)
        
        # 2. Create nested snapshot lines AND real Flock records
        for line in flock_lines_data:
            # Save to the Opening Position snapshot
            OpeningFlockLine.objects.create(
                position=position, 
                identifier=line['identifier'], 
                initial_count=line['initial_count']
            )
            
            # FIX: Use the individual arrival_date if provided, otherwise fallback to the global event_date
            individual_date = line.get('arrival_date') or validated_data['event_date']
            
            # Create the real, operational Flock record
            Flock.objects.create(
                farm=farm,
                identifier=line['identifier'],
                initial_count=line['initial_count'],
                arrival_date=individual_date, # <-- UPDATED: Uses individual date or global date
                breed=line.get('breed', ''),
                stage=line.get('stage', 'Chick')
            )
            
        # 3. Create stock snapshot lines
        for line in stock_lines_data:
            OpeningStockLine.objects.create(position=position, **line)
            
        return position