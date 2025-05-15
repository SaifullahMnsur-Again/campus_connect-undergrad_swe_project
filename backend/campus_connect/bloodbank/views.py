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
                blood_group = BloodGroup.objects.get(pk=pk)
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