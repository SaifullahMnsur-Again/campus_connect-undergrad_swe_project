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
    LostItemResolveSerializer, FoundItemResolveSerializer
)
from django.http import FileResponse
import logging

logger = logging.getLogger(__name__)

class AllItemsListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        # Fetch querysets
        lost_items = LostItem.objects.all()
        found_items = FoundItem.objects.all()
        
        # Serialize
        lost_serializer = SimpleLostItemSerializer(lost_items, many=True, context={'request': request})
        found_serializer = FoundItemSerializer(found_items, many=True, context={'request': request})
        
        # Combine and sort by created_at
        all_items = lost_serializer.data + found_serializer.data
        all_items.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_items = paginator.paginate_queryset(all_items, request)
        return paginator.get_paginated_response(paginated_items)

class LostItemListCreateView(generics.ListCreateAPIView):
    queryset = LostItem.objects.all()
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SimpleLostItemSerializer
        return LostItemSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FoundItemListCreateView(generics.ListCreateAPIView):
    queryset = FoundItem.objects.all()
    serializer_class = FoundItemSerializer
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LostItemDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            lost_item = LostItem.objects.get(pk=pk)
            serializer = SimpleLostItemSerializer(lost_item, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except LostItem.DoesNotExist:
            return Response({"message": "Lost item not found."}, status=status.HTTP_404_NOT_FOUND)

class FoundItemDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            found_item = FoundItem.objects.get(pk=pk)
            serializer = FoundItemSerializer(found_item, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except FoundItem.DoesNotExist:
            return Response({"message": "Found item not found."}, status=status.HTTP_404_NOT_FOUND)

class LostItemClaimView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = LostItemClaimSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(claimant=request.user)
            lost_item = LostItem.objects.get(pk=serializer.validated_data['lost_item'].pk)
            lost_item.status = 'claimed'
            lost_item.save()
            logger.info(f"Claim made by {request.user.email} for lost item {lost_item.title}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Claim failed: {serializer.errors}")
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class FoundItemClaimView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = FoundItemClaimSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(claimant=request.user)
            found_item = FoundItem.objects.get(pk=serializer.validated_data['found_item'].pk)
            found_item.status = 'claimed'
            found_item.save()
            logger.info(f"Claim made by {request.user.email} for found item {found_item.title}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Claim failed: {serializer.errors}")
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class LostItemResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            lost_item = LostItem.objects.get(pk=pk)
            if lost_item.user != request.user:
                return Response(
                    {"message": "Only the item owner can resolve it."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = LostItemResolveSerializer(data=request.data)
            if serializer.is_valid():
                item_status = serializer.validated_data['status']
                resolved_by = serializer.validated_data.get('resolved_by')
                if item_status == 'found' and resolved_by:
                    if not LostItemClaim.objects.filter(lost_item=lost_item, claimant=resolved_by).exists():
                        return Response(
                            {"message": "Resolved_by must be one of the claimants."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                lost_item.status = item_status
                lost_item.resolved_by = resolved_by
                lost_item.save()
                logger.info(f"Lost item {lost_item.title} resolved as {item_status} by {request.user.email}")
                return Response({"message": f"Lost item marked as {item_status}."}, status=status.HTTP_200_OK)
            return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except LostItem.DoesNotExist:
            return Response({"message": "Lost item not found."}, status=status.HTTP_404_NOT_FOUND)

class FoundItemResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            found_item = FoundItem.objects.get(pk=pk)
            if found_item.user != request.user:
                return Response(
                    {"message": "Only the item owner can resolve it."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = FoundItemResolveSerializer(data=request.data)
            if serializer.is_valid():
                item_status = serializer.validated_data['status']
                resolved_by = serializer.validated_data.get('resolved_by')
                if item_status == 'returned' and resolved_by:
                    if not FoundItemClaim.objects.filter(found_item=found_item, claimant=resolved_by).exists():
                        return Response(
                            {"message": "Resolved_by must be one of the claimants."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                found_item.status = item_status
                found_item.resolved_by = resolved_by
                found_item.save()
                logger.info(f"Found item {found_item.title} resolved as {item_status} by {request.user.email}")
                return Response({"message": f"Found item marked as {item_status}."}, status=status.HTTP_200_OK)
            return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except FoundItem.DoesNotExist:
            return Response({"message": "Found item not found."}, status=status.HTTP_404_NOT_FOUND)

class ResolvedItemsListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        lost_items = LostItem.objects.filter(status__in=['found', 'externally_found'])
        found_items = FoundItem.objects.filter(status__in=['returned', 'externally_returned'])
        lost_serializer = SimpleLostItemSerializer(lost_items, many=True, context={'request': request})
        found_serializer = FoundItemSerializer(found_items, many=True, context={'request': request})
        
        # Combine and sort by created_at
        all_items = lost_serializer.data + found_serializer.data
        all_items.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_items = paginator.paginate_queryset(all_items, request)
        return paginator.get_paginated_response(paginated_items)

class MediaAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            media = ItemMedia.objects.get(id=pk)
            # Check if user has access (owner of post/claim or claimant)
            user = request.user
            has_access = False
            if media.lost_item and (media.lost_item.user == user or 
                                   LostItemClaim.objects.filter(lost_item=media.lost_item, claimant=user).exists()):
                has_access = True
            elif media.found_item and (media.found_item.user == user or 
                                     FoundItemClaim.objects.filter(found_item=media.found_item, claimant=user).exists()):
                has_access = True
            elif media.lost_item_claim and media.lost_item_claim.claimant == user:
                has_access = True
            elif media.found_item_claim and media.found_item_claim.claimant == user:
                has_access = True

            if not has_access:
                return Response({"message": "You do not have permission to access this media."}, 
                               status=status.HTTP_403_FORBIDDEN)

            # Serve the file
            file_path = media.file.path
            content_type = 'application/octet-stream'
            if file_path.endswith(('.jpg', '.jpeg', '.png')):
                content_type = 'image/jpeg' if file_path.endswith(('.jpg', '.jpeg')) else 'image/png'
            elif file_path.endswith(('.mp4', '.mov')):
                content_type = 'video/mp4' if file_path.endswith('.mp4') else 'video/quicktime'

            return FileResponse(open(file_path, 'rb'), content_type=content_type)
        except ItemMedia.DoesNotExist:
            return Response({"message": "Media not found."}, status=status.HTTP_404_NOT_FOUND)
        except FileNotFoundError:
            return Response({"message": "Media file not found on server."}, status=status.HTTP_404_NOT_FOUND)