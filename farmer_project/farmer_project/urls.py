from django.contrib import admin
from django.urls import path, include

# ✅ ADD THIS LINE (VERY IMPORTANT)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),   # your app urls
]

# ✅ MEDIA FILES (Farmer photo, uploads, etc.)
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
