from . import views
from django.urls import path
from django.contrib.auth.views import LogoutView

app_name = 'dashboard'

urlpatterns = [
    path('home/', views.HomeView.as_view(), name = 'home'),
    path('logout/', views.LogoutView.as_view(), name ='logout'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('report_view/<int:id>/', views.Report.as_view(), name='reportview'),
    path('role_dispatch/', views.role_dispatch, name='role_dispatch'),
    path('add_recipient/', views.AddRecipient.as_view(), name = 'add'),
    path('confirmation/', views.Confirmation.as_view(), name = 'ok'),
    
]