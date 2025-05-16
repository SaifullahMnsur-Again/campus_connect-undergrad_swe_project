from rest_framework.views import APIView
from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from django.urls import reverse
from django.db.models import Q
from .models import BloodGroup, Donor, BloodRequest, BloodRequestDonor
from .serializers import BloodGroupSerializer, DonorSerializer, BloodRequestSerializer, BloodRequestDonorSerializer
from lostandfound.views import AdminPermission, UniversityAdminPermission
import logging

logger = logging.getLogger(__name__)

class BloodGroupView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        if pk:
            try:
                blood_group = BloodGroup.objects.get(name=pk)
                serializer = BloodGroupSerializer(blood_group)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except BloodGroup.DoesNotExist:
                return Response({"message": "Blood group not found."}, status=status.HTTP_404_NOT_FOUND)
        
        blood_groups = BloodGroup.objects.all()
        serializer = BloodGroupSerializer(blood_groups, many=True)
        return Response([item['name'] for item in serializer.data], status=status.HTTP_200_OK)

class DonorRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, 'donor_profile'):
            return Response({
                "message": "User is already registered as a donor."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = DonorSerializer(data=request.data)
        if serializer.is_valid():
            donor = serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DonorProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DonorSerializer

    def get(self, request):
        try:
            donor = request.user.donor_profile
            serializer = DonorSerializer(donor, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Donor.DoesNotExist:
            return Response({
                "message": "No donor profile found. To register as a donor use the url below.",
                "redirect": request.build_absolute_uri(reverse('donor-register'))
            }, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        try:
            donor = request.user.donor_profile
            serializer = DonorSerializer(donor, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": "Donor profile updated successfully.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Donor.DoesNotExist:
            return Response({
                "message": "No donor profile found. To register as a donor use the url below.",
                "redirect": request.build_absolute_uri(reverse('donor-register'))
            }, status=status.HTTP_404_NOT_FOUND)

class DonorWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            donor = request.user.donor_profile
            donor.delete()
            return Response({"message": "Donor profile withdrawn successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Donor.DoesNotExist:
            return Response({"message": "No donor profile found."}, status=status.HTTP_404_NOT_FOUND)

class DonorDetailView(APIView):
    serializer_class = DonorSerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            donor = Donor.objects.get(pk=pk)
            serializer = DonorSerializer(donor, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Donor.DoesNotExist:
            return Response({'message': 'Donor profile not found.'}, status=status.HTTP_404_NOT_FOUND)

class DonorListView(APIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        blood_group = request.query_params.get('blood_group', None)
        location = request.query_params.get('location', None)
        last_donated_before = request.query_params.get('last_donated_before', None)
        last_donated_after = request.query_params.get('last_donated_after', None)

        donors = Donor.objects.all()

        if blood_group:
            donors = donors.filter(user__blood_group__name=blood_group)
        if location:
            donors = donors.filter(preferred_location__icontains=location)
        if last_donated_before:
            try:
                donors = donors.filter(last_donated__lte=last_donated_before)
            except ValueError:
                return Response({"message": "Invalid date format for last_donated_before. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        if last_donated_after:
            try:
                donors = donors.filter(last_donated__gte=last_donated_after)
            except ValueError:
                return Response({"message": "Invalid date format for last_donated_after. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        paginator = self.pagination_class()
        paginated_donors = paginator.paginate_queryset(donors, request)
        serializer = DonorSerializer(paginated_donors, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

class BloodRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get_serializer_class(self):
        return BloodRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return BloodRequest.objects.filter(
                Q(status='open') |
                Q(user=user)
            )
        return BloodRequest.objects.filter(
            # approval_status='approved',
            status='open'
        )

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
            logger.info(f"Blood request '{serializer.instance.title}' created by {self.request.user.email}")
        except serializers.ValidationError as e:
            logger.error(f"Blood request creation failed for {self.request.user.email}: {e}")
            raise

class BloodRequestDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(
                pk=pk,
                # approval_status='approved',
                status='open'
            )
            serializer = BloodRequestSerializer(blood_request, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BloodRequest.DoesNotExist:
            return Response(
                {"error": "Blood request not found, not approved, or resolved."},
                status=status.HTTP_404_NOT_FOUND
            )

class BloodRequestDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
            if not (request.user == blood_request.user or UniversityAdminPermission().has_object_permission(request, self, blood_request)):
                return Response(
                    {"error": "You do not have permission to delete this request."},
                    status=status.HTTP_403_FORBIDDEN
                )
            blood_request.delete()
            logger.info(f"Blood request '{blood_request.title}' deleted by {request.user.email}")
            return Response({"message": "Blood request deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except BloodRequest.DoesNotExist:
            return Response({"error": "Blood request not found."}, status=status.HTTP_404_NOT_FOUND)

# class BloodRequestApprovalView(APIView):
#     permission_classes = [IsAuthenticated, UniversityAdminPermission]

#     def post(self, request, pk):
#         try:
#             blood_request = BloodRequest.objects.get(pk=pk)
#             if not UniversityAdminPermission().has_object_permission(request, self, blood_request):
#                 return Response(
#                     {"error": "You do not have permission to approve this request."},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
#             # serializer = BloodRequestApprovalSerializer(data=request.data)
#             # if serializer.is_valid():
#             #     blood_request.approval_status = serializer.validated_data['approval_status']
#             blood_request.save()
#             logger.info(f"Blood request '{blood_request.title}' set to '{blood_request.approval_status}' by {request.user.email}")
#             return Response(
#                 {"message": f"Blood request '{blood_request.title}' {blood_request.approval_status}."},
#                 status=status.HTTP_200_OK
#             )
#             # return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
#         except BloodRequest.DoesNotExist:
#             return Response({"error": "Blood request not found."}, status=status.HTTP_404_NOT_FOUND)

class BloodRequestDonorRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            donor = request.user.donor_profile
        except Donor.DoesNotExist:
            return Response({
                "message": "You must be registered as a donor to volunteer for a blood request.",
                "redirect": request.build_absolute_uri(reverse('donor-register'))
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = BloodRequestDonorSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            blood_request_donor = serializer.save()
            logger.info(f"Donor {request.user.email} registered for blood request ID {blood_request_donor.blood_request.pk}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Donor registration failed: {serializer.errors}")
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class BloodRequestDonorListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(
                pk=pk,
                status='open'
            )
            if not (request.user == blood_request.user or request.user.admin_level in ['university', 'app']):
                return Response(
                    {"error": "You do not have permission to view registered donors for this request."},
                    status=status.HTTP_403_FORBIDDEN
                )
            registered_donors = BloodRequestDonor.objects.filter(blood_request=blood_request)
            paginator = self.pagination_class()
            paginated_donors = paginator.paginate_queryset(registered_donors, request)
            serializer = BloodRequestDonorSerializer(paginated_donors, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        except BloodRequest.DoesNotExist:
            return Response(
                {"error": "Blood request not found, not approved, or resolved."},
                status=status.HTTP_404_NOT_FOUND
            )

# class BloodRequestApprovalSerializer(serializers.Serializer):
#     approval_status = serializers.ChoiceField(choices=['approved', 'rejected'])