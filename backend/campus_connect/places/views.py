from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from django.db.models import Q
from django.db import transaction
from .models import Place, PlaceType, PlaceMedia, PlaceUpdate
from .serializers import PlaceSerializer, PlaceTypeSerializer, PlaceSearchSerializer, PlaceUpdateSerializer
from universities.models import University, AcademicUnit
from .permissions import PlaceOwnerOrAdminPermission, UniversityAdminPermission
import logging

logger = logging.getLogger(__name__)

class PlaceListCreateView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = PlaceSerializer

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get_queryset(self):
        return Place.objects.filter(approval_status='approved').select_related('university', 'academic_unit', 'place_type')

    def perform_create(self, serializer):
        with transaction.atomic():
            if self.request.user.admin_level in ['university', 'app']:
                serializer.save(created_by=self.request.user, approval_status='approved')
            else:
                serializer.save(created_by=self.request.user)
            logger.info(f"Place '{serializer.instance.name}' created by {self.request.user.email}")

class UniversityPlacesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        root_places = Place.objects.filter(parent__isnull=True, approval_status='approved').select_related('university')
        serializer = PlaceSerializer(root_places, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class PlaceDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            place = Place.objects.get(pk=pk, approval_status='approved')
            serializer = PlaceSerializer(place, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Place.DoesNotExist:
            return Response({"error": "Place not found or not approved."}, status=status.HTTP_404_NOT_FOUND)

class PlaceUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            place = Place.objects.get(pk=pk, approval_status='approved')
            serializer = PlaceUpdateSerializer(data=request.data, context={'request': request, 'place': place})
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()
                    logger.info(f"Place update for '{place.name}' submitted by {request.user.email}")
                    return Response({
                        "message": "Place update submitted for approval.",
                        "data": serializer.data
                    }, status=status.HTTP_201_CREATED)
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Place.DoesNotExist:
            return Response({"error": "Place not found or not approved."}, status=status.HTTP_404_NOT_FOUND)

class PlaceDeleteView(APIView):
    permission_classes = [IsAuthenticated, PlaceOwnerOrAdminPermission]

    def delete(self, request, pk):
        try:
            place = Place.objects.get(pk=pk)
            if not PlaceOwnerOrAdminPermission().has_object_permission(request, self, place):
                return Response(
                    {"error": "You do not have permission to delete this place."},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Check for child places
            child_places = Place.objects.filter(parent=place)
            if child_places.exists():
                return Response(
                    {"error": "Cannot delete place with child places. Delete all child places first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            with transaction.atomic():
                place_name = place.name
                place.delete()
                logger.info(f"Place '{place_name}' deleted by {request.user.email}")
                return Response({"message": "Place deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Place.DoesNotExist:
            return Response({"error": "Place not found."}, status=status.HTTP_404_NOT_FOUND)

class PlaceSearchView(APIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        serializer = PlaceSearchSerializer(data=request.query_params, context={'request': request})
        if serializer.is_valid():
            places = Place.objects.filter(approval_status='approved').select_related('university', 'academic_unit', 'place_type')
            
            # Handle general search with raw query string
            raw_query = serializer.validated_data.get('raw_query')
            logger.debug(f"Processing raw query: {raw_query}")
            if raw_query:
                places = places.filter(
                    Q(name__icontains=raw_query) |
                    Q(university__name__icontains=raw_query) |
                    Q(university__short_name__icontains=raw_query) |
                    Q(academic_unit__name__icontains=raw_query) |
                    Q(academic_unit__short_name__icontains=raw_query)
                )
                logger.debug(f"Filtered places count: {places.count()}")
            else:
                # Handle specific field searches
                if serializer.validated_data.get('university'):
                    try:
                        university = University.objects.get(name=serializer.validated_data['university'])
                        places = places.filter(university=university)
                    except University.DoesNotExist:
                        return Response({"error": "University not found."}, status=status.HTTP_404_NOT_FOUND)
                if serializer.validated_data.get('place_type'):
                    try:
                        place_type = PlaceType.objects.get(name=serializer.validated_data['place_type'].lower())
                        places = places.filter(place_type=place_type)
                    except PlaceType.DoesNotExist:
                        return Response({"error": "Place type not found."}, status=status.HTTP_404_NOT_FOUND)
                if serializer.validated_data.get('name'):
                    name_query = serializer.validated_data['name']
                    places = places.filter(
                        Q(name__icontains=name_query) |
                        Q(university__short_name__icontains=name_query) |
                        Q(academic_unit__short_name__icontains=name_query)
                    )
                if serializer.validated_data.get('relative_location'):
                    places = places.filter(relative_location__icontains=serializer.validated_data['relative_location'])
                if serializer.validated_data.get('academic_unit'):
                    try:
                        academic_unit = AcademicUnit.objects.get(name=serializer.validated_data['academic_unit'])
                        places = places.filter(academic_unit=academic_unit)
                    except AcademicUnit.DoesNotExist:
                        return Response({"error": "Academic unit not found."}, status=status.HTTP_404_NOT_FOUND)

            paginator = self.pagination_class()
            paginated_places = paginator.paginate_queryset(places, request)
            serializer = PlaceSerializer(paginated_places, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class PlaceTypeListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        place_types = PlaceType.objects.all()
        serializer = PlaceTypeSerializer(place_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MediaAccessView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            media = PlaceMedia.objects.get(id=pk)
            if media.place and media.place.approval_status != 'approved':
                return Response({"error": "Media not accessible; place is not approved."}, status=status.HTTP_403_FORBIDDEN)
            if media.place_update and media.place_update.approval_status != 'approved':
                if not (request.user.is_authenticated and (
                    request.user == media.place_update.updated_by or
                    request.user.admin_level in ['university', 'app']
                )):
                    return Response({"error": "Media not accessible; update is not approved."}, status=status.HTTP_403_FORBIDDEN)
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
        except PlaceMedia.DoesNotExist:
            return Response({"error": "Media not found."}, status=status.HTTP_404_NOT_FOUND)
        except FileNotFoundError:
            return Response({"error": "Media file not found on server."}, status=status.HTTP_404_NOT_FOUND)

class PendingPlaceUpdatesView(APIView):
    permission_classes = [IsAuthenticated, UniversityAdminPermission]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        user = request.user
        if user.admin_level == 'university':
            updates = PlaceUpdate.objects.filter(
                university=user.university, approval_status='pending'
            ).select_related('place', 'university')
        else:
            updates = PlaceUpdate.objects.filter(approval_status='pending').select_related('place', 'university')
        paginator = self.pagination_class()
        paginated_updates = paginator.paginate_queryset(updates, request)
        serializer = PlaceUpdateSerializer(paginated_updates, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

class PlaceUpdateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            update = PlaceUpdate.objects.get(pk=pk)
            if not (request.user == update.updated_by or
                    request.user.admin_level in ['university', 'app']):
                return Response(
                    {"error": "You do not have permission to view this update."},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer = PlaceUpdateSerializer(update, context={'request': request})
            original_serializer = PlaceSerializer(update.place, context={'request': request})
            return Response({
                "original": original_serializer.data,
                "update": serializer.data
            }, status=status.HTTP_200_OK)
        except PlaceUpdate.DoesNotExist:
            return Response({"error": "Place update not found."}, status=status.HTTP_404_NOT_FOUND)

class PlaceUpdateApprovalView(APIView):
    permission_classes = [IsAuthenticated, UniversityAdminPermission]

    def post(self, request, pk):
        try:
            place_update = PlaceUpdate.objects.get(pk=pk)
            if not UniversityAdminPermission().has_object_permission(request, self, place_update):
                return Response(
                    {"error": "You do not have permission to approve this update."},
                    status=status.HTTP_403_FORBIDDEN
                )
            approval_status = request.data.get('approval_status')
            if approval_status not in ['approved', 'rejected']:
                return Response(
                    {"error": "Invalid approval_status. Use 'approved' or 'rejected'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            with transaction.atomic():
                place_update.approval_status = approval_status
                if approval_status == 'approved':
                    place = place_update.place
                    place.university = place_update.university or place.university
                    place.academic_unit = place_update.academic_unit
                    place.parent = place_update.parent
                    place.name = place_update.name or place.name
                    place.description = place_update.description or place.description
                    place.history = place_update.history or place.history
                    place.establishment_year = place_update.establishment_year or place.establishment_year
                    place.place_type = place_update.place_type or place.place_type
                    place.relative_location = place_update.relative_location or place.relative_location
                    place.latitude = place_update.latitude if place_update.latitude is not None else place.latitude
                    place.longitude = place_update.longitude if place_update.longitude is not None else place.longitude
                    place.maps_link = place_update.maps_link or place.maps_link
                    place.university_root = place_update.university_root
                    place.academic_unit_root = place_update.academic_unit_root
                    place.save()
                    for media in place_update.media.all():
                        media.place = place
                        media.place_update = None
                        media.save()
                place_update.save()
                logger.info(f"Place update '{place_update.place.name}' set to '{approval_status}' by {request.user.email}")
                return Response(
                    {"message": f"Place update '{place_update.place.name}' {approval_status}."},
                    status=status.HTTP_200_OK
                )
        except PlaceUpdate.DoesNotExist:
            return Response({"error": "Place update not found."}, status=status.HTTP_404_NOT_FOUND)