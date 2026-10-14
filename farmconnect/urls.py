from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from marketplace.views import home
urlpatterns = [path("system-admin/", admin.site.urls), path("accounts/", include("accounts.urls")), path("", home, name="home"), path("", include("marketplace.urls"))]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
