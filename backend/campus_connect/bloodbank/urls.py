from django.urls import path
from .views import (
    BloodGroupView,
    DonorRegisterView,
    DonorProfileView,
    DonorWithdrawView,
    DonorDetailView,
    DonorListView
)

urlpatterns = [
    path('bloodgroups/', BloodGroupView.as_view(), name='bloodgroup-list'),
    path('bloodgroups/<str:pk>/', BloodGroupView.as_view(), name='bloodgroup-detail'),
    path('donor/register/', DonorRegisterView.as_view(), name='donor-register'),
    path('donor/', DonorProfileView.as_view(), name='donor-profile'),
    path('donor/profile/', DonorProfileView.as_view(), name='donor-profile-explicit'),
    path('donor/withdraw/', DonorWithdrawView.as_view(), name='donor-withdraw'),
    path('donor/<int:pk>/', DonorDetailView.as_view(), name='donor-detail'),
    path('donors/', DonorListView.as_view(), name='donor-list'),  # New endpoint for donor list
]