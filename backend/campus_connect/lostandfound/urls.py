from django.urls import path, re_path
from .views import (
    AllItemsListView,
    LostItemListCreateView,
    FoundItemListCreateView,
    LostItemDetailView,
    FoundItemDetailView,
    LostItemClaimView,
    FoundItemClaimView,
    LostItemResolveView,
    FoundItemResolveView,
    ResolvedItemsListView,
    MediaAccessView
)

urlpatterns = [
    path('all/', AllItemsListView.as_view(), name='all-items-list'),
    path('lost/', LostItemListCreateView.as_view(), name='lost-item-list'),
    path('found/', FoundItemListCreateView.as_view(), name='found-item-list'),
    path('lost/<int:pk>/', LostItemDetailView.as_view(), name='lost-item-detail'),
    path('found/<int:pk>/', FoundItemDetailView.as_view(), name='found-item-detail'),
    path('lost/claim/', LostItemClaimView.as_view(), name='lost-item-claim'),
    path('found/claim/', FoundItemClaimView.as_view(), name='found-item-claim'),
    path('lost/<int:pk>/resolve/', LostItemResolveView.as_view(), name='lost-item-resolve'),
    path('found/<int:pk>/resolve/', FoundItemResolveView.as_view(), name='found-item-resolve'),
    path('resolved/', ResolvedItemsListView.as_view(), name='resolved-items-list'),
    re_path(r'^media/(?P<pk>[A-Za-z0-9_-]+)/$', MediaAccessView.as_view(), name='media-access'),
]