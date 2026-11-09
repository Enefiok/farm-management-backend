from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Unit, Item, UnitConversion, Party, StockMovement
from .serializers import UnitSerializer, ItemSerializer, UnitConversionSerializer, PartySerializer, StockMovementSerializer
from core.permissions import IsFarmMember

# --- UNITS (Global) ---
class UnitListCreateView(generics.ListCreateAPIView):
    serializer_class = UnitSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Unit.objects.all() 

# --- ITEMS LIST & CREATE (Farm-Scoped) ---
class ItemListCreateView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # CRITICAL: Only return ACTIVE items for the farm specified in the URL
        return Item.objects.filter(farm_id=self.kwargs['farm_pk'], is_active=True)

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'])

# --- ITEM DETAIL: UPDATE & ARCHIVE (Farm-Scoped) ---
# This is the missing piece that handles PATCH (edit) and DELETE (archive)
class ItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # We don't filter by is_active here so the user can still fetch it to edit or archive it
        return Item.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_destroy(self, instance):
        # SOFT DELETE: Archive the item instead of deleting it from the database
        instance.is_active = False
        instance.save()

# --- UNIT CONVERSIONS (Item-Scoped) ---
class UnitConversionListCreateView(generics.ListCreateAPIView):
    serializer_class = UnitConversionSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return UnitConversion.objects.filter(
            item__farm_id=self.kwargs['farm_pk'], 
            item_id=self.kwargs['item_pk']
        )

    def perform_create(self, serializer):
        serializer.save(item_id=self.kwargs['item_pk'])

# --- NEW: UNIT CONVERSION DETAIL (Edit/Delete a single conversion) ---
class UnitConversionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles GET (detail), PUT/PATCH (update), and DELETE for a single unit conversion.
    """
    serializer_class = UnitConversionSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return UnitConversion.objects.filter(
            item__farm_id=self.kwargs['farm_pk'],
            item_id=self.kwargs['item_pk']
        )

    def perform_destroy(self, instance):
        # HARD DELETE: Conversions can be safely deleted since they don't affect historical data
        instance.delete()

# --- PARTIES (Farm-Scoped) ---
class PartyListCreateView(generics.ListCreateAPIView):
    serializer_class = PartySerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        return Party.objects.filter(farm_id=self.kwargs['farm_pk'])

    def perform_create(self, serializer):
        serializer.save(farm_id=self.kwargs['farm_pk'])

# --- STOCK MOVEMENTS (Item-Scoped) ---
# NEW: This endpoint lets the frontend fetch the stock history for a specific item
class StockMovementListView(generics.ListAPIView):
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get_queryset(self):
        # Only return movements for the specific farm and item
        return StockMovement.objects.filter(
            farm_id=self.kwargs['farm_pk'], 
            item_id=self.kwargs['item_pk']
        ).order_by('-event_date', '-entry_timestamp')