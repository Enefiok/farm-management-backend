from django.urls import path
from .views import CreateFarmView, OpeningPositionCreateView

urlpatterns = [
    # GET /api/farms/ (List user's farms)
    # POST /api/farms/ (Create a new farm)
    path('', CreateFarmView.as_view(), name='farm-list-create'),
    
    # POST /api/farms/<farm_pk>/opening-position/
    path('<int:farm_pk>/opening-position/', OpeningPositionCreateView.as_view(), name='opening-position-create'),
]