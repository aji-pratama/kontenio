"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Customize admin site
admin.site.site_header = "🎬 AI Video Factory"
admin.site.site_title = "Video Factory Admin"
admin.site.index_title = "Welcome to the AI Video Factory"

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

