from . import views
from django.urls import path

app_name = 'dashboard'
urlpatterns = [

    path('home/', views.BillboardView.as_view(), name = 'home'),
    path('logout/', views.LogoutView.as_view(), name ='logout'),
    path('role_dispatch/', views.role_dispatch, name='role_dispatch'),

    ####### Recipients ########
    path('add_recipient/', views.AddRecipient.as_view(), name = 'add'),
    path('recipient_delete/', views.DeleteRecipient.as_view(), name = 'recipient_delete'),
    ####### Messages ##########

    path('messages/', views.HomeView.as_view(), name='messages'),
    path('messages/create/', views.MessageView.as_view(), name = 'messages_create'),
    path('report_detail/<int:id>/', views.MessageDetail.as_view(), name='reportview'),
    path('messages/inbox', views.InboxView.as_view(), name = 'inbox'),
    path('delete_report/<int:pk>', views.MessageDelete.as_view(), name = 'report_delete'),
    path('update_report/<int:pk>', views.MessageUpdate.as_view(), name = 'report_update'),
    ####### TASKS ############
    path('tasks/', views.TasksList.as_view(), name = 'tasks_list'),
    path('tasks/<int:pk>/', views.TaskDetail.as_view(), name='task_detail'),
    path('tasks/create', views.TaskForm.as_view(), name = 'task_form'),
    path('tasks/delete/<int:pk>', views.TaskDelete.as_view(), name = 'task_delete'),
    ######### PICTURES #########
    path('pic_picture/<int:pk>', views.stream_file, name='pic_picture'),

    ####### MANAGE ###########
    path('team/', views.TeamView.as_view(), name = 'team'),
    path('create-task, views', views.TaskManageCreate.as_view(), name = 'task_manage_create'),
    path('tasks/update/<int:pk>', views.TaskUpdate.as_view(), name = 'task_manage_update'),
    #######TEAM ##########
    path('team/update/<int:pk>', views.TeamUpdate.as_view(), name='team_update'),
    path('team/completed/', views.TeamCompletedTask.as_view(), name='team_completed'),



] 