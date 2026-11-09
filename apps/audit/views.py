from rest_framework import generics, permissions
from django.utils import timezone
from .models import Adjustment
from .serializers import AdjustmentSerializer
from core.permissions import IsFarmMember

class AdjustmentCreateView(generics.CreateAPIView):
    serializer_class = AdjustmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def perform_create(self, serializer):
        # Save the adjustment with the current farm, user, and today's date
        serializer.save(
            farm_id=self.kwargs['farm_pk'], 
            created_by=self.request.user,
            event_date=timezone.now().date()  # <-- FIX: Provides the required event_date
        )

class AdjustmentListView(generics.ListAPIView):
    serializer_class = AdjustmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # Order by entry_timestamp (from BaseModel) instead of created_at
        return Adjustment.objects.filter(farm_id=self.kwargs['farm_pk']).order_by('-entry_timestamp')