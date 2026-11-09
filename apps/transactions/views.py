from rest_framework import generics, permissions
from django.utils import timezone
from .models import Purchase, Sale, Expense
from .serializers import PurchaseSerializer, SaleSerializer, ExpenseSerializer, PaymentSerializer
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

class SaleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    NEW: Handles GET (detail), PUT/PATCH (update), and DELETE for a single sale.
    This allows the Edit button to actually update the sale and trigger the stock adjustment logic.
    """
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return Sale.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_update(self, serializer):
        serializer.save(created_by=self.request.user)

class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return Expense.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'], created_by=self.request.user)

class PaymentCreateView(generics.CreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def perform_create(self, serializer):
        # Save the payment with the current farm, user, and today's date
        serializer.save(
            farm_id=self.kwargs['farm_pk'], 
            created_by=self.request.user,
            event_date=timezone.now().date() 
        )