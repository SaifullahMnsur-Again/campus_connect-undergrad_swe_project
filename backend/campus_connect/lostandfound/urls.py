from django.urls import path
from .views import (
    AllItemsListView, PendingItemsListView, LostItemListCreateView, FoundItemListCreateView,
    LostItemDetailView, FoundItemDetailView, LostItemClaimView, FoundItemClaimView,
    LostItemResolveView, FoundItemResolveView, LostItemApprovalView, FoundItemApprovalView,
    ResolvedItemsListView, MyClaimsListView, MyPostsListView,
    LostItemClaimsListView, FoundItemClaimsListView, HistoryView, MediaAccessView
)

app_name = 'lostandfound'

urlpatterns = [
    path('all/', AllItemsListView.as_view(), name='all-items'),
    path('pending/', PendingItemsListView.as_view(), name='pending-items'),
    path('resolved/', ResolvedItemsListView.as_view(), name='resolved-items'),
    path('lost/', LostItemListCreateView.as_view(), name='lost-items'),
    path('found/', FoundItemListCreateView.as_view(), name='found-items'),
    path('lost/<int:pk>/', LostItemDetailView.as_view(), name='lost-item-detail'),
    path('found/<int:pk>/', FoundItemDetailView.as_view(), name='found-item-detail'),
    path('lost/claim/', LostItemClaimView.as_view(), name='lost-item-claim'),
    path('found/claim/', FoundItemClaimView.as_view(), name='found-item-claim'),
    path('lost/<int:pk>/resolve/', LostItemResolveView.as_view(), name='lost-item-resolve'),
    path('found/<int:pk>/resolve/', FoundItemResolveView.as_view(), name='found-item-resolve'),
    path('lost/<int:pk>/approve/', LostItemApprovalView.as_view(), name='lost-item-approve'),
    path('found/<int:pk>/approve/', FoundItemApprovalView.as_view(), name='found-item-approve'),
    path('my-claims/', MyClaimsListView.as_view(), name='my-claims'),
    path('my-posts/', MyPostsListView.as_view(), name='my-posts'),
    path('lost/<int:pk>/claims/', LostItemClaimsListView.as_view(), name='lost-item-claims'),
    path('found/<int:pk>/claims/', FoundItemClaimsListView.as_view(), name='found-item-claims'),
    path('history/', HistoryView.as_view(), name='history'),
    path('media/<str:pk>/', MediaAccessView.as_view(), name='media-access'),
]