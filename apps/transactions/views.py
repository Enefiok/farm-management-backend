from rest_framework import generics, permissions
from .models import Purchase, Sale, Expense
from .serializers import PurchaseSerializer, SaleSerializer, ExpenseSerializer
from core.permissions import IsFarmMember

class PurchaseListCreateView(generics.ListCreateAPIView):
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return Purchase.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'], created_by=self.request.user)

class SaleListCreateView(generics.ListCreateAPIView):
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return Sale.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'], created_by=self.request.user)

class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return Expense.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'], created_by=self.request.user)