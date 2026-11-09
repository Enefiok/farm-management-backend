from django.urls import path
from . import views

urlpatterns = [
    path('', views.AdjustmentListView.as_view(), name='adjustment-list'),
    path('create/', views.AdjustmentCreateView.as_view(), name='adjustment-create'),
]