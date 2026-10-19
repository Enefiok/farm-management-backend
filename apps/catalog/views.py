from rest_framework import generics, permissions
from .models import Item, Party
from .serializers import ItemSerializer, PartySerializer
from core.permissions import IsFarmMember, IsOwnerOrAdmin

class ItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # CRITICAL: Only return items for the farm specified in the URL
        return Item.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        # CRITICAL: Automatically assign the farm from the URL, ignoring any farm_id sent by the client
        farm_id = self.kwargs['farm_pk']
        serializer.save(farm_id=farm_id)

class PartyListCreateView(generics.ListCreateAPIView):
    serializer_class = PartySerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return Party.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'])