from django.urls import path
from .views import (
    PlaceListCreateView, UniversityPlacesView, PlaceDetailView,
    PlaceUpdateView, PlaceDeleteView, PlaceSearchView,
    PlaceTypeListView, MediaAccessView, PendingPlaceUpdatesView,
    PlaceUpdateDetailView, PlaceUpdateApprovalView
)

app_name = 'places'

urlpatterns = [
    path('', PlaceListCreateView.as_view(), name='place-list'),
    path('universities/', UniversityPlacesView.as_view(), name='university-places'),
    path('<int:pk>/', PlaceDetailView.as_view(), name='place-detail'),
    path('<int:pk>/update/', PlaceUpdateView.as_view(), name='place-update'),
    path('<int:pk>/delete/', PlaceDeleteView.as_view(), name='place-delete'),
    path('search/', PlaceSearchView.as_view(), name='place-search'),
    path('place-types/', PlaceTypeListView.as_view(), name='place-type-list'),
    path('media/<int:pk>/', MediaAccessView.as_view(), name='media-access'),
    path('pending/', PendingPlaceUpdatesView.as_view(), name='pending-updates'),
    path('updates/<int:pk>/', PlaceUpdateDetailView.as_view(), name='place-update-detail'),
    path('updates/<int:pk>/approve/', PlaceUpdateApprovalView.as_view(), name='place-update-approve'),
]