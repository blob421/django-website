"""
URL configuration for portal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))s
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include, reverse
from dashboard.views import CustomLoginView
from dashboard.views import CustomRegistration
from dashboard.forms import CustomRegistrationForm
from django.conf.urls.static import	static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/' ,include('api.urls')),
    path('accounts/register/',
        CustomRegistration.as_view(form_class=CustomRegistrationForm),
        name='django_registration_register'),

    path("accounts/", include("django_registration.backends.one_step.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('', CustomLoginView.as_view(template_name='dashboard/login.html')),
    path('__debug__/', include('debug_toolbar.urls')),

]
urlpatterns+= static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns+= static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

