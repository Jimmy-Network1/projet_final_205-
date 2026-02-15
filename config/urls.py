"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include  # Ajoutez 'include'
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

handler404 = "voitures.views.handler404"
handler500 = "voitures.views.handler500"

def healthz(_request):
    return HttpResponse("ok", content_type="text/plain")

urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path('admin/', admin.site.urls),
    path('', include('voitures.urls')),  # Ajoutez cette ligne
]

# Pour servir les fichiers médias (utile en démo / hébergement simple)
if getattr(settings, "SERVE_MEDIA", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
