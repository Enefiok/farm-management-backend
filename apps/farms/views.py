from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from .models import Farm, FarmMembership, FarmSetting, OpeningPosition
from .serializers import CreateFarmSerializer, OpeningPositionSerializer
from apps.accounts.models import Membership
from core.models import AuditEvent
from core.permissions import IsFarmMember


class CreateFarmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # --- NEW: GET method to list the user's farms ---
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

    # --- EXISTING: POST method to create a farm ---
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

                # 6. Return the farm details WITH the settings
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