from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import RedirectView

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/img/logo.png')), # Or your specific favicon path
    path('', include('store.urls')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customize admin site header
admin.site.site_header = "Jay Bn Poultry Farm — Admin"
admin.site.site_title = "Poultry Farm Admin"
admin.site.index_title = "Farm Management Dashboard"
