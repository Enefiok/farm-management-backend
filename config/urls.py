from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.transactions.views import PurchaseListCreateView, SaleListCreateView, ExpenseListCreateView
from apps.catalog.views import ItemListCreateView, PartyListCreateView
from apps.operations.views import FlockListCreateView, ProductionRecordListCreateView, FarmActivityListCreateView
import os
from apps.accounts.views import (
    RegisterView, LoginView, LogoutView, MeView, 
    InviteUserView, AcceptInvitationView, FarmMembersView,
    PasswordResetRequestView, PasswordResetConfirmView
)
from apps.farms.views import CreateFarmView

@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "ok",
        "version": "1.0",
        "environment": os.environ.get('DJANGO_SETTINGS_ENV', 'local')
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    
    # Auth Endpoints
    path('api/auth/register/', RegisterView.as_view(), name='auth-register'),
    path('api/auth/login/', LoginView.as_view(), name='auth-login'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('api/auth/me/', MeView.as_view(), name='auth-me'),
    
    # Password Reset Endpoints
    path('api/auth/password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('api/auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Farm Endpoints
    path('api/farms/', CreateFarmView.as_view(), name='create-farm'),
    
    # User & Invitation Endpoints
    path('api/invitations/', InviteUserView.as_view(), name='invite-user'),
    path('api/invitations/accept/', AcceptInvitationView.as_view(), name='accept-invitation'),
    path('api/farms/<int:farm_pk>/members/', FarmMembersView.as_view(), name='farm-members'),
    
    # Catalog Endpoints (Scoped to Farm)
    path('api/farms/<int:farm_pk>/items/', ItemListCreateView.as_view(), name='farm-items'),
    path('api/farms/<int:farm_pk>/parties/', PartyListCreateView.as_view(), name='farm-parties'),
    
    # Operations Endpoints (Scoped to Farm)
    path('api/farms/<int:farm_pk>/flocks/', FlockListCreateView.as_view(), name='farm-flocks'),
    path('api/farms/<int:farm_pk>/production/', ProductionRecordListCreateView.as_view(), name='farm-production'),
    path('api/farms/<int:farm_pk>/activities/', FarmActivityListCreateView.as_view(), name='farm-activities'),
    
    # OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Transactions Endpoints (Scoped to Farm)
    path('api/farms/<int:farm_pk>/purchases/', PurchaseListCreateView.as_view(), name='farm-purchases'),
    path('api/farms/<int:farm_pk>/sales/', SaleListCreateView.as_view(), name='farm-sales'),
    path('api/farms/<int:farm_pk>/expenses/', ExpenseListCreateView.as_view(), name='farm-expenses'),

]