from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/bloodbank/', include('bloodbank.urls')),
    path('api/universities/', include('universities.urls')),  # Add universities app
    path('api/lostandfound/', include('lostandfound.urls')),  # Add lostandfound app
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)