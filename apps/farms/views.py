from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from .models import Farm, FarmMembership, FarmSetting, OpeningPosition
from .serializers import CreateFarmSerializer, OpeningPositionSerializer
from apps.accounts.models import Membership
from apps.catalog.models import Item, Unit, UnitConversion
from core.models import AuditEvent
from core.permissions import IsFarmMember


class CreateFarmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # --- GET method to list the user's farms ---
    def get(self, request):
        # Find all memberships for the logged-in user
        memberships = FarmMembership.objects.filter(
            user=request.user
        ).select_related('farm', 'farm__settings')

        data = []
        for membership in memberships:
            farm = membership.farm
            settings_obj = getattr(farm, 'settings', None)
            
            # Build the settings object (fallback to defaults if missing)
            settings_data = {
                "currency": settings_obj.currency,
                "timezone": settings_obj.timezone,
                "unit_system": settings_obj.unit_system
            } if settings_obj else {
                "currency": "NGN", "timezone": "Africa/Lagos", "unit_system": "metric"
            }

            data.append({
                "farm": {
                    "id": farm.id,
                    "name": farm.name,
                    "location": farm.location,
                    "contact_info": farm.contact_info,
                    "settings": settings_data
                },
                "role": membership.role
            })

        return Response(data, status=status.HTTP_200_OK)

    # --- POST method to create a farm ---
    def post(self, request):
        serializer = CreateFarmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Pop the settings fields out so they aren't passed to Farm.objects.create()
        currency = serializer.validated_data.pop('currency', 'NGN')
        timezone = serializer.validated_data.pop('timezone', 'Africa/Lagos')
        unit_system = serializer.validated_data.pop('unit_system', 'metric')

        try:
            with transaction.atomic():
                # 1. Find the user's Account (created during registration)
                user_account_membership = Membership.objects.filter(user=request.user).first()
                if not user_account_membership:
                    return Response(
                        {"error": "User must belong to an account to create a farm."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 2. Create the Farm and link it to the Account
                farm = serializer.save(account=user_account_membership.account)

                # 3. Create the FarmSetting with frontend-provided values (or defaults)
                FarmSetting.objects.create(
                    farm=farm,
                    currency=currency,
                    timezone=timezone,
                    unit_system=unit_system
                )

                # 4. Create the FarmMembership (Assign user as OWNER)
                FarmMembership.objects.create(
                    user=request.user,
                    farm=farm,
                    role=FarmMembership.RoleChoices.OWNER
                )

                # 5. Write an Audit Event
                AuditEvent.objects.create(
                    actor=request.user,
                    farm=farm,
                    action="farm_created",
                    details={
                        "farm_name": farm.name,
                        "currency": currency,
                        "timezone": timezone,
                        "unit_system": unit_system
                    }
                )

                # 6. Create default items for the new farm
                self._create_default_items(farm)

                # 7. Return the farm details WITH the settings
                return Response({
                    "farm": {
                        "id": farm.id, 
                        "name": farm.name,
                        "location": farm.location,
                        "contact_info": farm.contact_info
                    },
                    "settings": {
                        "currency": currency,
                        "timezone": timezone,
                        "unit_system": unit_system
                    },
                    "role": "OWNER",
                    "message": "Farm created successfully."
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _create_default_items(self, farm):
        """
        Creates essential default items for a new farm so the farmer has something
        to work with immediately (Egg, Layer Mash) with proper unit conversions.
        """
        # Get or create global units
        egg_unit, _ = Unit.objects.get_or_create(
            name="Egg", defaults={"abbreviation": "egg"}
        )
        tray_unit, _ = Unit.objects.get_or_create(
            name="Tray", defaults={"abbreviation": "tray"}
        )
        crate_unit, _ = Unit.objects.get_or_create(
            name="Crate", defaults={"abbreviation": "crate"}
        )
        kg_unit, _ = Unit.objects.get_or_create(
            name="Kilogram", defaults={"abbreviation": "kg"}
        )
        bag_unit, _ = Unit.objects.get_or_create(
            name="Bag", defaults={"abbreviation": "bag"}
        )

        # Create Egg item (Egg Product category)
        # FIX: Removed 'created_by' because the Item model doesn't have that field
        egg_item = Item.objects.create(
            farm=farm,
            name="Egg",
            category="EGG",
            base_unit=egg_unit,
            is_stock_tracked=True,
            is_active=True
        )
        # 1 Tray = 30 Eggs, 1 Crate = 30 Eggs
        UnitConversion.objects.create(item=egg_item, unit=tray_unit, factor=30, is_base=False)
        UnitConversion.objects.create(item=egg_item, unit=crate_unit, factor=30, is_base=False)

        # Create Layer Mash item (Feed category)
        mash_item = Item.objects.create(
            farm=farm,
            name="Layer Mash",
            category="FEED",
            base_unit=kg_unit,
            is_stock_tracked=True,
            is_active=True
        )
        # 1 Bag = 25 Kilograms
        UnitConversion.objects.create(item=mash_item, unit=bag_unit, factor=25, is_base=False)


class OpeningPositionCreateView(generics.CreateAPIView):
    """
    Creates the opening position for a farm (birds, stock, balances).
    Forces classification='OPENING' and captures created_by automatically.
    """
    serializer_class = OpeningPositionSerializer
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def perform_create(self, serializer):
        # Automatically link to the farm from the URL and force OPENING classification
        serializer.save(
            farm_id=self.kwargs['farm_pk'], 
            classification='OPENING',
            created_by=self.request.user
        )