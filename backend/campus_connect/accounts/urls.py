from django.urls import path
from .views import (
    RegisterUserView,
    EmailVerificationView,
    LoginView,
    LogoutView,
    UserListView,
    ProfileView,
    UserDetailView
)

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', UserListView.as_view(), name='user-list'),
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]