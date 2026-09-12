"""
URL configuration for dashboard-interna project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from dashboard import views
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import include, path
from django.contrib import admin
from decouple import config

urlpatterns = [
    path(config('ADMIN_URL', default='admin/').strip('/') + '/', admin.site.urls),
    path("buzon/api/request-pin", views.request_pin),
    path("buzon/api/upload", views.upload_file),
    path("buzon/api/recursos", views.list_recursos),
    path("proyectos-iniciales/", views.initial_projects_view, name="initial_projects"),
    path("proyectos-iniciales/generacion/<int:generation>/", views.initial_projects_list_view, name="initial_projects_list"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

