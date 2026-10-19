from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Account, Membership, Invitation
from apps.farms.models import Farm, FarmMembership

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        attrs['email'] = attrs['email'].lower().strip()
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
            
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        return user

class InviteUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    farm_id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=Membership.RoleChoices.choices)

    def validate_farm_id(self, value):
        if not Farm.objects.filter(id=value).exists():
            raise serializers.ValidationError("Farm not found.")
        return value

    def validate_role(self, value):
        user = self.context['request'].user
        inviter_membership = Membership.objects.filter(user=user, farm_id=self.initial_data.get('farm_id')).first()
        
        if inviter_membership and inviter_membership.role == Membership.RoleChoices.STAFF:
            raise serializers.ValidationError("Staff members cannot invite users.")
            
        if value in [Membership.RoleChoices.OWNER, Membership.RoleChoices.ADMINISTRATOR]:
            if not inviter_membership or inviter_membership.role != Membership.RoleChoices.OWNER:
                raise serializers.ValidationError("Only Owners can assign Owner or Administrator roles.")
        return value

class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])