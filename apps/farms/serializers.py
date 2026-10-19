from rest_framework import serializers
from .models import Farm

class CreateFarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ['name', 'location', 'contact_info']
        # Note: We do NOT include 'account' here. The backend will automatically 
        # assign the farm to the user's account for security.