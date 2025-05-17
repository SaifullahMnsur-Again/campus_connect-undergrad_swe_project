from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls', namespace='accounts')),
    path('api/bloodbank/', include('bloodbank.urls', namespace='bloodbank')),
    path('api/universities/', include('universities.urls', namespace='universities')),
    path('api/lostandfound/', include('lostandfound.urls', namespace='lostandfound')),
    path('api/places/', include('places.urls', namespace='places')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)