from rest_framework import permissions
from apps.farms.models import FarmMembership

class IsFarmMember(permissions.BasePermission):
    """
    Allows access only if the user has ANY membership in the target farm.
    Used for read-only or general farm endpoints.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Look for farm_pk in the URL (e.g., /api/farms/<farm_pk>/items/)
        # If it's a farm-level endpoint, it might just be 'pk'
        farm_pk = view.kwargs.get('farm_pk') or view.kwargs.get('pk')
        
        if not farm_pk:
            return True # Let the view handle queryset scoping if no farm_pk in URL

        return FarmMembership.objects.filter(
            user=request.user,
            farm_id=farm_pk
        ).exists()

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access ONLY if the user is an Owner or Administrator of the target farm.
    Used for sensitive actions like inviting users or changing settings.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        farm_pk = view.kwargs.get('farm_pk') or view.kwargs.get('pk')
        if not farm_pk:
            return False
            
        return FarmMembership.objects.filter(
            user=request.user,
            farm_id=farm_pk,
            role__in=[FarmMembership.RoleChoices.OWNER, FarmMembership.RoleChoices.ADMINISTRATOR]
        ).exists()