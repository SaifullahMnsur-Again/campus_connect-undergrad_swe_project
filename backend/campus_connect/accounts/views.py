import logging
import random
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate
from django.urls import reverse
from django.db import transaction
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from .serializers import (
    RegisterSerializer, EmailVerificationSerializer, LoginSerializer, 
    UserSerializer, UserListSerializer, UserProfileSerializer
)
from .models import User, VerificationCode

logger = logging.getLogger(__name__)

class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Register a new user and send a verification code."""
        with transaction.atomic():
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.create(serializer.validated_data)
                logger.debug(f"Registering user: {user.email}, blood_group: {user.blood_group}")
                
                code = str(random.randint(100000, 999999))
                logger.debug(f"\033[33mVerification code for {user.email}: {code}\033[0m")

                expires_at = timezone.now() + timedelta(minutes=15)
                VerificationCode.objects.create(
                    user=user,
                    code=code,
                    purpose=VerificationCode.Purpose.EMAIL_VERIFICATION,
                    expires_at=expires_at
                )

                return Response({
                    "message": "User registered, please verify your email.",
                    "redirect": reverse('verify-email')
                }, status=status.HTTP_201_CREATED)
            logger.error(f"Registration failed: {serializer.errors}")
            return Response({
                "message": serializer.errors,
                "redirect": None
            }, status=status.HTTP_400_BAD_REQUEST)

class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Verify a user's email with a code."""
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            try:
                user = User.objects.get(email=email)
                verification = VerificationCode.objects.filter(
                    user=user,
                    code=code,
                    purpose=VerificationCode.Purpose.EMAIL_VERIFICATION,
                    expires_at__gt=timezone.now()
                ).first()
                if verification:
                    user.is_active = user.is_verified = True
                    user.save()
                    verification.delete()
                    return Response({
                        'message': 'Email verified successfully.',
                        'redirect': reverse('login')
                    }, status=status.HTTP_200_OK)
                return Response({
                    'message': 'Invalid or expired code.',
                    'redirect': None
                }, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({
                    'message': 'User not found.',
                    'redirect': None
                }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'message': serializer.errors,
            'redirect': None
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate a user and return a token."""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                if not user.is_active:
                    logger.warning(f"Login failed: User {email} is inactive.")
                    return Response({
                        'message': 'Account is inactive or unverified.',
                        'redirect': None
                    }, status=status.HTTP_400_BAD_REQUEST)
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                token, created = Token.objects.get_or_create(user=user)
                logger.info(f"Login successful for {email}, token created: {created}, token: {token.key}")
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user, context={'request': request}).data,
                    'profile_url': request.build_absolute_uri(reverse('user-profile')),
                    'redirect': None
                }, status=status.HTTP_200_OK)
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    logger.warning(f"Login failed: User {email} is inactive.")
                    return Response({
                        'message': 'Account is inactive or unverified.',
                        'redirect': None
                    }, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                pass
            logger.warning(f"Login failed: Invalid credentials for {email}")
            return Response({
                'message': 'Invalid credentials.',
                'redirect': None
            }, status=status.HTTP_400_BAD_REQUEST)
        logger.error(f"Login validation error: {serializer.errors}")
        return Response({
            'message': serializer.errors,
            'redirect': None
        }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Log out a user by deleting their token."""
        try:
            request.user.auth_token.delete()
            logger.info(f"Logout successful for {request.user.email}")
            return Response({
                'message': 'Logged out successfully.',
                'redirect': None
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout error for {request.user.email}: {str(e)}")
            return Response({
                'message': str(e),
                'redirect': None
            }, status=status.HTTP_400_BAD_REQUEST)

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

class ProfileView(APIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve the authenticated user's profile."""
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update the authenticated user's profile."""
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Profile updated successfully for {user.email}")
            return Response({
                "message": "Profile updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        logger.error(f"Profile update failed for {user.email}: {serializer.errors}")
        return Response({
            "message": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get(self, request, pk):
        """Retrieve a user's details by ID."""
        try:
            user = User.objects.get(pk=pk)
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)