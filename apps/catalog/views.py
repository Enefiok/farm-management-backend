from rest_framework import generics, permissions
from .models import Unit, Item, UnitConversion, Party
from .serializers import UnitSerializer, ItemSerializer, UnitConversionSerializer, PartySerializer
from core.permissions import IsFarmMember

# --- UNITS (Global) ---
class UnitListCreateView(generics.ListCreateAPIView):
    serializer_class = UnitSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Units are shared across the platform
    queryset = Unit.objects.all() 

# --- ITEMS (Farm-Scoped) ---
class ItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # CRITICAL: Only return items for the farm specified in the URL
        return Item.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        # CRITICAL: Automatically assign the farm from the URL
        serializer.save(farm_id=self.kwargs['farm_pk'])

# --- UNIT CONVERSIONS (Item-Scoped) ---
class UnitConversionListCreateView(generics.ListCreateAPIView):
    serializer_class = UnitConversionSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # Ensure the item belongs to the farm before showing conversions
        return UnitConversion.objects.filter(
            item__farm_id=self.kwargs['farm_pk'], 
            item_id=self.kwargs['item_pk']
        )

    def perform_create(self, serializer):
        # Lock the conversion to the specific item from the URL
        serializer.save(item_id=self.kwargs['item_pk'])

# --- PARTIES (Farm-Scoped) ---
class PartyListCreateView(generics.ListCreateAPIView):
    serializer_class = PartySerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return Party.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'])