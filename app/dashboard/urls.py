from . import views
from django.urls import path
from django.contrib.auth.views import LogoutView

app_name = 'dashboard'

urlpatterns = [
    path('home/', views.HomeView.as_view(), name = 'home'),
    path('logout/', views.LogoutView.as_view(), name ='logout'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('report_view/<int:id>/', views.Report.as_view(), name='reportview'),
    path('delete_report/<int:pk>', views.DeleteReport.as_view(), name = 'report_delete'),
    path('update_report/<int:pk>', views.UpdateReport.as_view(), name = 'report_update'),
    path('role_dispatch/', views.role_dispatch, name='role_dispatch'),
    path('add_recipient/', views.AddRecipient.as_view(), name = 'add'),
   
    path('recipient_delete/', views.DeleteRecipient.as_view(), name = 'recipient_delete'),
    path('confirmation/', views.Confirmation.as_view(), name = 'ok'),
    
]