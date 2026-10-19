from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .serializers import (
    RegisterSerializer, InviteUserSerializer, AcceptInvitationSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from .models import Account, Membership, Invitation
from apps.farms.models import Farm, FarmMembership
from core.permissions import IsOwnerOrAdmin, IsFarmMember
from core.models import AuditEvent
from django.contrib.auth import get_user_model

User = get_user_model()

# --- AUTH VIEWS ---

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                user = serializer.save()
                account = Account.objects.create(name=f"{user.full_name}'s Account")
                Membership.objects.create(
                    user=user,
                    account=account,
                    role=Membership.RoleChoices.OWNER
                )
                login(request, user)

                return Response({
                    "user": {"email": user.email, "full_name": user.full_name},
                    "message": "Registration successful."
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Please provide both email and password."}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return Response({
                "user": {"email": user.email, "full_name": user.full_name},
                "message": "Login successful."
            })
        else:
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."})

class MeView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user
        membership = Membership.objects.filter(user=user).first()
        
        return Response({
            "email": user.email,
            "full_name": user.full_name,
            "account_id": membership.account.id if membership else None,
            "role": membership.role if membership else None
        })

# --- PASSWORD RESET VIEWS ---

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower().strip()

        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # SECURITY: In production, you would send an email here.
            # For local development/testing, we return the token in the response.
            return Response({
                "message": "If an account exists with this email, a reset link has been sent.",
                "uid": uid, 
                "token": token 
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Security rule: Never reveal if an email exists or not
            return Response({"message": "If an account exists with this email, a reset link has been sent."}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, serializer.validated_data['token']):
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password has been reset successfully."})
        else:
            return Response({"error": "Invalid token or user ID."}, status=status.HTTP_400_BAD_REQUEST)

# --- INVITATION & USER MANAGEMENT VIEWS ---

class InviteUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request):
        serializer = InviteUserSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower().strip()
        farm_id = serializer.validated_data['farm_id']
        role = serializer.validated_data['role']

        farm = Farm.objects.get(id=farm_id)

        if FarmMembership.objects.filter(farm=farm, user__email=email).exists():
            return Response({"error": "User is already a member of this farm."}, status=status.HTTP_400_BAD_REQUEST)

        if Invitation.objects.filter(farm=farm, email=email, status=Invitation.StatusChoices.PENDING).exists():
            return Response({"error": "An active invitation already exists for this email."}, status=status.HTTP_400_BAD_REQUEST)

        invitation = Invitation.objects.create(
            email=email,
            farm=farm,
            role=role,
            created_by=request.user
        )

        AuditEvent.objects.create(
            actor=request.user,
            farm=farm,
            action="user_invited",
            details={"email": email, "role": role, "invitation_id": invitation.id}
        )

        return Response({
            "message": "Invitation sent successfully.",
            "token": invitation.token 
        }, status=status.HTTP_201_CREATED)

class AcceptInvitationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        try:
            invitation = Invitation.objects.get(token=token, status=Invitation.StatusChoices.PENDING)
        except Invitation.DoesNotExist:
            return Response({"error": "Invalid or expired invitation."}, status=status.HTTP_400_BAD_REQUEST)

        if invitation.expires_at < timezone.now():
            invitation.status = Invitation.StatusChoices.EXPIRED
            invitation.save()
            return Response({"error": "This invitation has expired."}, status=status.HTTP_400_BAD_REQUEST)

        if invitation.email.lower() != request.user.email.lower():
            return Response({"error": "This invitation is for a different email address."}, status=status.HTTP_403_FORBIDDEN)

        FarmMembership.objects.create(
            user=request.user,
            farm=invitation.farm,
            role=invitation.role
        )

        invitation.status = Invitation.StatusChoices.ACCEPTED
        invitation.save()

        AuditEvent.objects.create(
            actor=request.user,
            farm=invitation.farm,
            action="invitation_accepted",
            details={"role": invitation.role}
        )

        return Response({"message": "Successfully joined the farm!"})

class FarmMembersView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsFarmMember]

    def get(self, request, farm_pk):
        memberships = FarmMembership.objects.filter(farm_id=farm_pk).select_related('user')
        data = [
            {
                "id": m.id,
                "user_email": m.user.email,
                "full_name": m.user.full_name,
                "role": m.role,
                "joined_at": m.joined_at
            }
            for m in memberships
        ]
        return Response(data)