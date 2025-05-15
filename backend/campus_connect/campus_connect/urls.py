from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/bloodbank/', include('bloodbank.urls')),
    path('api/universities/', include('universities.urls')),  # Add universities app
]