from django.urls import path
from .views import (
    BloodGroupView,
    DonorRegisterView,
    DonorProfileView,
    DonorWithdrawView,
    DonorDetailView,
    DonorListView,
    BloodRequestListCreateView,
    BloodRequestDetailView,
    # BloodRequestApprovalView,
    BloodRequestDeleteView,
    BloodRequestDonorRegisterView,
    BloodRequestDonorListView
)

urlpatterns = [
    path('bloodgroups/', BloodGroupView.as_view(), name='bloodgroup-list'),
    path('bloodgroups/<str:pk>/', BloodGroupView.as_view(), name='bloodgroup-detail'),
    path('donor/register/', DonorRegisterView.as_view(), name='donor-register'),
    path('donor/', DonorProfileView.as_view(), name='donor-profile'),
    path('donor/profile/', DonorProfileView.as_view(), name='donor-profile-explicit'),
    path('donor/withdraw/', DonorWithdrawView.as_view(), name='donor-withdraw'),
    path('donor/<int:pk>/', DonorDetailView.as_view(), name='donor-detail'),
    path('donors/', DonorListView.as_view(), name='donor-list'),
    path('requests/', BloodRequestListCreateView.as_view(), name='blood-request-list'),
    path('requests/<int:pk>/', BloodRequestDetailView.as_view(), name='blood-request-detail'),
    # path('requests/<int:pk>/approve/', BloodRequestApprovalView.as_view(), name='blood-request-approve'),
    path('requests/<int:pk>/delete/', BloodRequestDeleteView.as_view(), name='blood-request-delete'),
    path('requests/donor/register/', BloodRequestDonorRegisterView.as_view(), name='blood-request-donor-register'),
    path('requests/<int:pk>/donors/', BloodRequestDonorListView.as_view(), name='blood-request-donor-list'),
]