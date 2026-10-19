from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Flock, ProductionRecord, FarmActivity
from .serializers import FlockSerializer, ProductionRecordSerializer, FarmActivitySerializer
from core.permissions import IsFarmMember

class FlockListCreateView(generics.ListCreateAPIView):
    serializer_class = FlockSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return Flock.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'])

class ProductionRecordListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductionRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return ProductionRecord.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        # Automatically set the farm and the user who created it (from BaseModel)
        serializer.save(farm_id=self.kwargs['farm_pk'], created_by=self.request.user)

class FarmActivityListCreateView(generics.ListCreateAPIView):
    serializer_class = FarmActivitySerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return FarmActivity.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'], created_by=self.request.user)