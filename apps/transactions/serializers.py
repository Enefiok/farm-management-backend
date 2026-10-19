from rest_framework import serializers
from .models import Purchase, Sale, Expense

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['id', 'supplier', 'item', 'quantity', 'unit_cost', 'total_cost', 'notes', 'event_date', 'classification']
        # Note: farm and created_by are handled automatically by the View and BaseModel

class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = ['id', 'customer', 'item', 'quantity', 'unit_price', 'total_amount', 'notes', 'event_date', 'classification']

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'payee', 'category', 'amount', 'description', 'event_date', 'classification']