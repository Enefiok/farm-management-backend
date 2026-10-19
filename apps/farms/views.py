from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import Farm, FarmMembership, FarmSetting
from .serializers import CreateFarmSerializer
from apps.accounts.models import Membership
from core.models import AuditEvent

class CreateFarmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateFarmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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

                # 3. Create the FarmSetting (Defaults: NGN, Africa/Lagos, metric)
                FarmSetting.objects.create(farm=farm)

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
                    details={"farm_name": farm.name}
                )

                return Response({
                    "farm": {"id": farm.id, "name": farm.name},
                    "role": "OWNER",
                    "message": "Farm created successfully."
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)