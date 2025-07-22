from . import views
from django.urls import path

app_name = 'dashboard'
urlpatterns = [
    
    path('home/', views.HomeView.as_view(), name = 'home'),
    path('logout/', views.LogoutView.as_view(), name ='logout'),
    path('role_dispatch/', views.role_dispatch, name='role_dispatch'),

    ####### Recipients ########
    path('add_recipient/', views.AddRecipient.as_view(), name = 'add'),
    path('recipient_delete/', views.DeleteRecipient.as_view(), name = 'recipient_delete'),
    ####### Messages ##########

    path('reports/', views.MessageView.as_view(), name='reports'),
    path('report_detail/<int:id>/', views.MessageDetail.as_view(), name='reportview'),
    path('delete_report/<int:pk>', views.MessageDelete.as_view(), name = 'report_delete'),
    path('update_report/<int:pk>', views.MessageUpdate.as_view(), name = 'report_update'),
  
]