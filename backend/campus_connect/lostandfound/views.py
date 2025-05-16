from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import MultiPartParser, FormParser
from .models import LostItem, FoundItem, LostItemClaim, FoundItemClaim, ItemMedia
from .serializers import (
    SimpleLostItemSerializer, LostItemSerializer, FoundItemSerializer,
    LostItemClaimSerializer, FoundItemClaimSerializer,
    LostItemResolveSerializer, FoundItemResolveSerializer,
    LostItemApprovalSerializer, FoundItemApprovalSerializer,
    HistorySerializer
)
from django.http import FileResponse
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class AdminPermission:
    """Permission class for university or app-wide admins."""
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.admin_level in ['university', 'app']

class UniversityAdminPermission(AdminPermission):
    """Permission class for admins with university-specific access."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.admin_level == 'app':
            return True
        return user.admin_level == 'university' and obj.university == user.university

class PostOwnerOrAdminPermission(AdminPermission):
    """Permission class for post owners or authorized admins."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.admin_level == 'app':
            return True
        if user.admin_level == 'university' and obj.university == user.university:
            return True
        return user == obj.user

class AllItemsListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        """
        Lists all approved, unresolved lost and found items.
        Includes post_type ('lost' or 'found'), is_admin, detail_url, claims_url.
        """
        lost_items = LostItem.objects.filter(
            approval_status='approved',
            status__in=['open', 'claimed']
        )
        found_items = FoundItem.objects.filter(
            approval_status='approved',
            status__in=['open', 'claimed']
        )

        lost_serializer = SimpleLostItemSerializer(lost_items, many=True, context={'request': request})
        found_serializer = FoundItemSerializer(found_items, many=True, context={'request': request})

        all_items = lost_serializer.data + found_serializer.data
        all_items.sort(key=lambda x: x['created_at'], reverse=True)

        paginator = self.pagination_class()
        paginated_items = paginator.paginate_queryset(all_items, request)
        return paginator.get_paginated_response(paginated_items)

class PendingItemsListView(APIView):
    permission_classes = [IsAuthenticated, AdminPermission]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        """
        Lists pending lost and found items for admins.
        Includes post_type ('lost' or 'found'), is_admin, detail_url, claims_url, approve_url.
        """
        user = request.user
        if user.admin_level == 'university':
            lost_items = LostItem.objects.filter(
                university=user.university, approval_status='pending'
            )
            found_items = FoundItem.objects.filter(
                university=user.university, approval_status='pending'
            )
        else:  # app-wide admin
            lost_items = LostItem.objects.filter(approval_status='pending')
            found_items = FoundItem.objects.filter(approval_status='pending')

        lost_serializer = SimpleLostItemSerializer(lost_items, many=True, context={'request': request})
        found_serializer = FoundItemSerializer(found_items, many=True, context={'request': request})

        all_items = lost_serializer.data + found_serializer.data
        all_items.sort(key=lambda x: x['created_at'], reverse=True)

        paginator = self.pagination_class()
        paginated_items = paginator.paginate_queryset(all_items, request)
        return paginator.get_paginated_response(paginated_items)

class LostItemListCreateView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get_serializer_class(self):
        return SimpleLostItemSerializer if self.request.method == 'GET' else LostItemSerializer

    def get_queryset(self):
        """
        Lists lost items. Non-owners see approved, unresolved posts.
        Owners see all their posts. Includes post_type, is_admin, detail_url, claims_url, resolve_url.
        """
        user = self.request.user
        if user.is_authenticated:
            return LostItem.objects.filter(
                Q(approval_status='approved', status__in=['open', 'claimed']) |
                Q(user=user)
            )
        return LostItem.objects.filter(
            approval_status='approved',
            status__in=['open', 'claimed']
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, approval_status='pending')
        logger.info(f"Lost item '{serializer.instance.title}' created by {self.request.user.email}")

class FoundItemListCreateView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get_serializer_class(self):
        return FoundItemSerializer

    def get_queryset(self):
        """
        Lists found items. Non-owners see approved, unresolved posts.
        Owners see all their posts. Includes post_type, is_admin, detail_url, claims_url, resolve_url.
        """
        user = self.request.user
        if user.is_authenticated:
            return FoundItem.objects.filter(
                Q(approval_status='approved', status__in=['open', 'claimed']) |
                Q(user=user)
            )
        return FoundItem.objects.filter(
            approval_status='approved',
            status__in=['open', 'claimed']
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, approval_status='pending')
        logger.info(f"Found item '{serializer.instance.title}' created by {self.request.user.email}")

class LostItemDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """
        Retrieves a lost item. Only approved, unresolved posts are accessible.
        Includes post_type ('lost'), is_admin, detail_url, claims_url.
        """
        try:
            lost_item = LostItem.objects.get(
                pk=pk,
                approval_status='approved',
                status__in=['open', 'claimed']
            )
            serializer = SimpleLostItemSerializer(lost_item, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except LostItem.DoesNotExist:
            return Response(
                {"error": "Lost item not found, not approved, or resolved."},
                status=status.HTTP_404_NOT_FOUND
            )

class FoundItemDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """
        Retrieves a found item. Only approved, unresolved posts are accessible.
        Includes post_type ('found'), is_admin, detail_url, claims_url.
        """
        try:
            found_item = FoundItem.objects.get(
                pk=pk,
                approval_status='approved',
                status__in=['open', 'claimed']
            )
            serializer = FoundItemSerializer(found_item, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except FoundItem.DoesNotExist:
            return Response(
                {"error": "Found item not found, not approved, or resolved."},
                status=status.HTTP_404_NOT_FOUND
            )

class LostItemClaimView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """
        Creates a claim for a lost item. Only approved, open posts can be claimed.
        Prevents self-claims and duplicates via serializer validation.
        """
        serializer = LostItemClaimSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(claimant=request.user)
            logger.info(f"Claim created by {request.user.email} for lost item ID {serializer.validated_data['lost_item'].pk}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Claim creation failed: {serializer.errors}")
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class FoundItemClaimView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """
        Creates a claim for a found item. Only approved, open posts can be claimed.
        Prevents self-claims and duplicates via serializer validation.
        """
        serializer = FoundItemClaimSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(claimant=request.user)
            logger.info(f"Claim created by {request.user.email} for found item ID {serializer.validated_data['found_item'].pk}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Claim creation failed: {serializer.errors}")
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class LostItemResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        Resolves a lost item. Only approved, unresolved posts can be resolved by owners.
        Validates resolved_by against claimants.
        """
        try:
            lost_item = LostItem.objects.get(
                pk=pk,
                approval_status='approved',
                status__in=['open', 'claimed']
            )
            if lost_item.user != request.user:
                return Response(
                    {"error": "Only the item owner can resolve this item."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = LostItemResolveSerializer(data=request.data)
            if serializer.is_valid():
                item_status = serializer.validated_data['status']
                resolved_by = serializer.validated_data.get('resolved_by')
                if item_status == 'found' and resolved_by:
                    if not LostItemClaim.objects.filter(lost_item=lost_item, claimant=resolved_by).exists():
                        return Response(
                            {"error": "Resolved_by must be one of the claimants."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                lost_item.status = item_status
                lost_item.resolved_by = resolved_by
                lost_item.save()
                logger.info(f"Lost item '{lost_item.title}' resolved as '{item_status}' by {request.user.email}")
                return Response({"message": f"Lost item resolved as '{item_status}'."}, status=status.HTTP_200_OK)
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except LostItem.DoesNotExist:
            return Response(
                {"error": "Lost item not found, not approved, or already resolved."},
                status=status.HTTP_404_NOT_FOUND
            )

class FoundItemResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """
        Resolves a found item. Only approved, unresolved posts can be resolved by owners.
        Validates resolved_by against claimants.
        """
        try:
            found_item = FoundItem.objects.get(
                pk=pk,
                approval_status='approved',
                status__in=['open', 'claimed']
            )
            if found_item.user != request.user:
                return Response(
                    {"error": "Only the item owner can resolve this item."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = FoundItemResolveSerializer(data=request.data)
            if serializer.is_valid():
                item_status = serializer.validated_data['status']
                resolved_by = serializer.validated_data.get('resolved_by')
                if item_status == 'returned' and resolved_by:
                    if not FoundItemClaim.objects.filter(found_item=found_item, claimant=resolved_by).exists():
                        return Response(
                            {"error": "Resolved_by must be one of the claimants."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                found_item.status = item_status
                found_item.resolved_by = resolved_by
                found_item.save()
                logger.info(f"Found item '{found_item.title}' resolved as '{item_status}' by {request.user.email}")
                return Response({"message": f"Found item resolved as '{item_status}'."}, status=status.HTTP_200_OK)
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except FoundItem.DoesNotExist:
            return Response(
                {"error": "Found item not found, not approved, or already resolved."},
                status=status.HTTP_404_NOT_FOUND
            )

class LostItemApprovalView(APIView):
    permission_classes = [IsAuthenticated, UniversityAdminPermission]

    def post(self, request, pk):
        """
        Approves or rejects a lost item. Only accessible to authorized admins.
        """
        try:
            lost_item = LostItem.objects.get(pk=pk)
            if not UniversityAdminPermission().has_object_permission(request, self, lost_item):
                return Response(
                    {"error": "You do not have permission to approve this item."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = LostItemApprovalSerializer(data=request.data)
            if serializer.is_valid():
                lost_item.approval_status = serializer.validated_data['approval_status']
                lost_item.save()
                logger.info(f"Lost item '{lost_item.title}' set to '{lost_item.approval_status}' by {request.user.email}")
                return Response(
                    {"message": f"Lost item '{lost_item.title}' {lost_item.approval_status}."},
                    status=status.HTTP_200_OK
                )
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except LostItem.DoesNotExist:
            return Response({"error": "Lost item not found."}, status=status.HTTP_404_NOT_FOUND)

class FoundItemApprovalView(APIView):
    permission_classes = [IsAuthenticated, UniversityAdminPermission]

    def post(self, request, pk):
        """
        Approves or rejects a found item. Only accessible to authorized admins.
        """
        try:
            found_item = FoundItem.objects.get(pk=pk)
            if not UniversityAdminPermission().has_object_permission(request, self, found_item):
                return Response(
                    {"error": "You do not have permission to approve this item."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = FoundItemApprovalSerializer(data=request.data)
            if serializer.is_valid():
                found_item.approval_status = serializer.validated_data['approval_status']
                found_item.save()
                logger.info(f"Found item '{found_item.title}' set to '{found_item.approval_status}' by {request.user.email}")
                return Response(
                    {"message": f"Found item '{found_item.title}' {found_item.approval_status}."},
                    status=status.HTTP_200_OK
                )
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except FoundItem.DoesNotExist:
            return Response({"error": "Found item not found."}, status=status.HTTP_404_NOT_FOUND)

class ResolvedItemsListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        """
        Lists approved, resolved lost and found items.
        Includes post_type ('lost' or 'found'), is_admin, detail_url, claims_url.
        """
        lost_items = LostItem.objects.filter(
            approval_status='approved',
            status__in=['found', 'externally_found']
        )
        found_items = FoundItem.objects.filter(
            approval_status='approved',
            status__in=['returned', 'externally_returned']
        )

        lost_serializer = SimpleLostItemSerializer(lost_items, many=True, context={'request': request})
        found_serializer = FoundItemSerializer(found_items, many=True, context={'request': request})

        all_items = lost_serializer.data + found_serializer.data
        all_items.sort(key=lambda x: x['created_at'], reverse=True)

        paginator = self.pagination_class()
        paginated_items = paginator.paginate_queryset(all_items, request)
        return paginator.get_paginated_response(paginated_items)

class MyClaimsListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        """
        Lists all claims made by the authenticated user.
        Only claims on approved, unresolved posts are included.
        """
        lost_claims = LostItemClaim.objects.filter(claimant=request.user)
        found_claims = FoundItemClaim.objects.filter(claimant=request.user)

        lost_serializer = LostItemClaimSerializer(lost_claims, many=True, context={'request': request})
        found_serializer = FoundItemClaimSerializer(found_claims, many=True, context={'request': request})

        all_claims = lost_serializer.data + found_serializer.data
        all_claims.sort(key=lambda x: x['created_at'], reverse=True)

        paginator = self.pagination_class()
        paginated_items = paginator.paginate_queryset(all_claims, request)
        return paginator.get_paginated_response(paginated_items)

class MyPostsListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        """
        Lists all posts (lost and found) created by the authenticated user.
        Includes unapproved and resolved posts, with post_type, is_admin, detail_url, claims_url, resolve_url, approve_url.
        """
        lost_items = LostItem.objects.filter(user=request.user)
        found_items = FoundItem.objects.filter(user=request.user)

        lost_serializer = SimpleLostItemSerializer(lost_items, many=True, context={'request': request})
        found_serializer = FoundItemSerializer(found_items, many=True, context={'request': request})

        all_posts = lost_serializer.data + found_serializer.data
        all_posts.sort(key=lambda x: x['created_at'], reverse=True)

        paginator = self.pagination_class()
        paginated_items = paginator.paginate_queryset(all_posts, request)
        return paginator.get_paginated_response(paginated_items)

class LostItemClaimsListView(APIView):
    permission_classes = [IsAuthenticated, PostOwnerOrAdminPermission]
    pagination_class = LimitOffsetPagination

    def get(self, request, pk):
        """
        Lists all claims on a specific lost item.
        Only approved, unresolved posts are accessible.
        """
        try:
            lost_item = LostItem.objects.get(
                pk=pk,
                approval_status='approved',
                status__in=['open', 'claimed']
            )
            if not PostOwnerOrAdminPermission().has_object_permission(request, self, lost_item):
                return Response(
                    {"error": "You do not have permission to view claims for this item."},
                    status=status.HTTP_403_FORBIDDEN
                )
            claims = LostItemClaim.objects.filter(lost_item=lost_item)
            serializer = LostItemClaimSerializer(claims, many=True, context={'request': request})
            paginator = self.pagination_class()
            paginated_items = paginator.paginate_queryset(serializer.data, request)
            return paginator.get_paginated_response(paginated_items)
        except LostItem.DoesNotExist:
            return Response(
                {"error": "Lost item not found, not approved, or resolved."},
                status=status.HTTP_404_NOT_FOUND
            )

class FoundItemClaimsListView(APIView):
    permission_classes = [IsAuthenticated, PostOwnerOrAdminPermission]
    pagination_class = LimitOffsetPagination

    def get(self, request, pk):
        """
        Lists all claims on a specific found item.
        Only approved, unresolved posts are accessible.
        """
        try:
            found_item = FoundItem.objects.get(
                pk=pk,
                approval_status='approved',
                status__in=['open', 'claimed']
            )
            if not PostOwnerOrAdminPermission().has_object_permission(request, self, found_item):
                return Response(
                    {"error": "You do not have permission to view claims for this item."},
                    status=status.HTTP_403_FORBIDDEN
                )
            claims = FoundItemClaim.objects.filter(found_item=found_item)
            serializer = FoundItemClaimSerializer(claims, many=True, context={'request': request})
            paginator = self.pagination_class()
            paginated_items = paginator.paginate_queryset(serializer.data, request)
            return paginator.get_paginated_response(paginated_items)
        except FoundItem.DoesNotExist:
            return Response(
                {"error": "Found item not found, not approved, or resolved."},
                status=status.HTTP_404_NOT_FOUND
            )

class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieves the authenticated user's activity history.
        Includes all posts (unapproved, unresolved, resolved), claims made, and claims received.
        Posts include post_type, is_admin, detail_url, claims_url, resolve_url, approve_url.
        """
        serializer = HistorySerializer({}, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class MediaAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Provides access to media files for authorized users.
        Owners access all their posts' media; others access approved, unresolved posts' media if claimed or admin.
        """
        try:
            media = ItemMedia.objects.get(id=pk)
            user = request.user
            has_access = False
            if media.lost_item:
                if (media.lost_item.approval_status == 'approved' and 
                    media.lost_item.status in ['open', 'claimed']):
                    if (
                        media.lost_item.user == user or
                        LostItemClaim.objects.filter(lost_item=media.lost_item, claimant=user).exists() or
                        user.admin_level in ['app', 'university']
                    ):
                        has_access = True
                elif media.lost_item.user == user:
                    has_access = True
            elif media.found_item:
                if (media.found_item.approval_status == 'approved' and 
                    media.found_item.status in ['open', 'claimed']):
                    if (
                        media.found_item.user == user or
                        FoundItemClaim.objects.filter(found_item=media.found_item, claimant=user).exists() or
                        user.admin_level in ['app', 'university']
                    ):
                        has_access = True
                elif media.found_item.user == user:
                    has_access = True
            elif media.lost_item_claim and media.lost_item_claim.claimant == user:
                has_access = True
            elif media.found_item_claim and media.found_item_claim.claimant == user:
                has_access = True
            elif user.admin_level in ['university', 'app']:
                has_access = True

            if not has_access:
                return Response(
                    {"error": "You do not have permission to access this media."},
                    status=status.HTTP_403_FORBIDDEN
                )

            file_path = media.file.path
            content_type = 'application/octet-stream'
            if file_path.endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            elif file_path.endswith('.png'):
                content_type = 'image/png'
            elif file_path.endswith('.mp4'):
                content_type = 'video/mp4'
            elif file_path.endswith('.mov'):
                content_type = 'video/quicktime'

            return FileResponse(open(file_path, 'rb'), content_type=content_type)
        except ItemMedia.DoesNotExist:
            return Response({"error": "Media not found."}, status=status.HTTP_404_NOT_FOUND)
        except FileNotFoundError:
            return Response({"error": "Media file not found on server."}, status=status.HTTP_404_NOT_FOUND)