from rest_framework import generics, permissions
from .models import Flock, ProductionRecord, FarmActivity
from .serializers import FlockSerializer, ProductionRecordSerializer, FarmActivitySerializer
from core.permissions import IsFarmMember

class FlockListCreateView(generics.ListCreateAPIView):
    serializer_class = FlockSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # Order by newest first (Flock uses created_at)
        return Flock.objects.filter(farm_id=self.kwargs['farm_pk']).order_by('-created_at', '-id')

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'], created_by=self.request.user)


class ProductionRecordListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductionRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # Order by newest first (event_date, then id)
        return ProductionRecord.objects.filter(farm_id=self.kwargs['farm_pk']).order_by('-event_date', '-id')

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'], created_by=self.request.user)


class FarmActivityListCreateView(generics.ListCreateAPIView):
    serializer_class = FarmActivitySerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # Order by newest first (event_date, then id)
        return FarmActivity.objects.filter(farm_id=self.kwargs['farm_pk']).order_by('-event_date', '-id')

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'], created_by=self.request.user)