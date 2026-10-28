from rest_framework import serializers
from .models import Purchase, PurchaseLine, Sale, SaleLine, Expense

class PurchaseLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseLine
        fields = ['item', 'quantity', 'unit_price', 'total']

class PurchaseSerializer(serializers.ModelSerializer):
    lines = PurchaseLineSerializer(many=True)

    class Meta:
        model = Purchase
        fields = ['id', 'farm', 'party', 'event_date', 'classification', 'total_amount', 'notes', 'lines', 'entry_timestamp', 'created_by']
        read_only_fields = ['id', 'farm', 'entry_timestamp', 'created_by', 'total_amount']
        extra_kwargs = {'classification': {'read_only': True, 'default': 'LIVE'}}

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        purchase = Purchase.objects.create(**validated_data)
        for line in lines_data:
            PurchaseLine.objects.create(purchase=purchase, **line)
        return purchase

class SaleLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleLine
        fields = ['item', 'quantity', 'unit_price', 'total']

class SaleSerializer(serializers.ModelSerializer):
    lines = SaleLineSerializer(many=True)

    class Meta:
        model = Sale
        fields = ['id', 'farm', 'party', 'event_date', 'classification', 'total_amount', 'notes', 'lines', 'entry_timestamp', 'created_by']
        read_only_fields = ['id', 'farm', 'entry_timestamp', 'created_by', 'total_amount']
        extra_kwargs = {'classification': {'read_only': True, 'default': 'LIVE'}}

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        sale = Sale.objects.create(**validated_data)
        for line in lines_data:
            SaleLine.objects.create(sale=sale, **line)
        return sale

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'farm', 'party', 'category', 'amount', 'event_date', 'classification', 'notes', 'entry_timestamp', 'created_by']
        read_only_fields = ['id', 'farm', 'entry_timestamp', 'created_by']
        extra_kwargs = {'classification': {'read_only': True, 'default': 'LIVE'}}