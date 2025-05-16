from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from django.urls import reverse
from .models import BloodGroup, Donor
from .serializers import BloodGroupSerializer, DonorSerializer

class BloodGroupView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        """
        Retrieve a list of blood group names or a single blood group by ID.
        Returns a list of names (e.g., ['A+', 'B+', ...]) for the list view.
        """
        if pk:
            try:
                blood_group = BloodGroup.objects.get(name=pk)
                serializer = BloodGroupSerializer(blood_group)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except BloodGroup.DoesNotExist:
                return Response({"message": "Blood group not found."}, status=status.HTTP_404_NOT_FOUND)
        
        blood_groups = BloodGroup.objects.all()
        serializer = BloodGroupSerializer(blood_groups, many=True)
        # Return only the list of names
        return Response([item['name'] for item in serializer.data], status=status.HTTP_200_OK)

class DonorRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Register a user as a donor."""
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
        """Retrieve the authenticated user's donor profile."""
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
        """Update the authenticated user's donor profile."""
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
        """Withdraw the authenticated user's donor profile."""
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
        """Retrieve a donor's profile by ID."""
        try:
            donor = Donor.objects.get(pk=pk)
            serializer = DonorSerializer(donor, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Donor.DoesNotExist:
            return Response({'message': 'Donor profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        

class DonorListView(APIView):
    permission_classes = [AllowAny]  # Adjust permissions as needed
    pagination_class = LimitOffsetPagination

    def get(self, request):
        """
        Retrieve a list of donors with optional filtering by blood group, location, and last donated date.
        Query parameters:
        - blood_group: Filter by blood group name (e.g., 'A+')
        - location: Filter by preferred location (partial match)
        - last_donated_before: Filter donors who last donated before this date (YYYY-MM-DD)
        - last_donated_after: Filter donors who last donated after this date (YYYY-MM-DD)
        """
        # Get query parameters
        blood_group = request.query_params.get('blood_group', None)
        location = request.query_params.get('location', None)
        last_donated_before = request.query_params.get('last_donated_before', None)
        last_donated_after = request.query_params.get('last_donated_after', None)

        # Start with all donors
        donors = Donor.objects.all()

        # Apply filters
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

        # Apply pagination
        paginator = self.pagination_class()
        paginated_donors = paginator.paginate_queryset(donors, request)

        # Serialize data
        serializer = DonorSerializer(paginated_donors, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)