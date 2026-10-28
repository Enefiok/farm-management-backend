from django.urls import path
from .views import FlockListCreateView, ProductionRecordListCreateView, FarmActivityListCreateView

urlpatterns = [
    # GET & POST /api/farms/<farm_pk>/flocks/
    path('<int:farm_pk>/flocks/', FlockListCreateView.as_view(), name='flock-list-create'),
    
    # GET & POST /api/farms/<farm_pk>/production/
    path('<int:farm_pk>/production/', ProductionRecordListCreateView.as_view(), name='production-list-create'),
    
    # GET & POST /api/farms/<farm_pk>/activities/
    path('<int:farm_pk>/activities/', FarmActivityListCreateView.as_view(), name='activity-list-create'),
]