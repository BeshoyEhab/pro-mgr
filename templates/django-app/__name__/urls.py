"""
URL configuration for {{name}} project.
"""

from django.contrib import admin
from django.urls import path
from django.http import JsonResponse


def index(request):
    """Root endpoint."""
    return JsonResponse({
        "message": "Welcome to {{name}}!",
        "version": "0.1.0"
    })


def health(request):
    """Health check endpoint."""
    return JsonResponse({"status": "healthy"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('health/', health, name='health'),
]
