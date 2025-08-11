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
    path('messages/forward/<int:pk>', views.MessageForward.as_view(), name='message_forward'),
    path('report_detail/<int:id>/', views.MessageDetail.as_view(), name='reportview'),
    path('messages/inbox', views.InboxView.as_view(), name = 'inbox'),
    path('delete_report/<int:pk>', views.MessageDelete.as_view(), name = 'report_delete'),
    path('update_report/<int:pk>', views.MessageUpdate.as_view(), name = 'report_update'),
    ####### TASKS ############
    path('tasks/', views.TasksList.as_view(), name = 'tasks_list'),
    path('tasks/<int:pk>/', views.TaskDetail.as_view(), name='task_detail'),
    path('tasks/create', views.TaskCreate.as_view(), name = 'task_form'),
    path('tasks/delete/<int:pk>', views.TaskDelete.as_view(), name = 'task_delete'),
    path('tasks/completed/<int:pk>', views.TaskSubmit.as_view(), name='task_submit'),
    ######### PICTURES #########
    path('pic_picture/<int:pk>', views.stream_file, name='pic_picture'),
    path('pic_picture_completed_task/<int:pk>', views.stream_completed_task_img, name='stream_completed_task_img'),
    ####### MANAGE ###########
    path('team/', views.TeamView.as_view(), name = 'team'),
    path('tasks/completed/<int:pk>/', views.TaskCompletedDetail.as_view(), name='task_completed_detail'),
    path('tasks/create/', views.TaskManageCreate.as_view(), name = 'task_manage_create'),
    path('tasks/update/<int:pk>', views.TaskUpdate.as_view(), name = 'task_manage_update'),
    path('tasks/completed/approve/<int:pk>', views.TeamCompletedApprove.as_view(), 
         name = 'task_approve'),

    ####### SCHEDULES ########
    path('schedules', views.ScheduleView.as_view(), name = 'schedule_view'),
    path('schedules/<int:pk>', views.ScheduleDetail.as_view(), name = 'schedule_detail'),
    path('schedules/manage', views.ScheduleManage.as_view(), name = 'schedule_manage'),
    path('schedules/update/<int:pk>', views.ScheduleUpdate.as_view(), 
         name = 'schedule_update'),
    path('schedules/user/<int:pk>/availability', views.AvailabilityForm.as_view(), 
         name='availability'),
    path('schedules/user/<int:pk>/request', views.ScheduleChangeRequest.as_view(),
          name='schedule_request'),
 
    #######TEAM ##########
    path('team/update/<int:pk>', views.TeamUpdate.as_view(), name='team_update'),
    path('team/completed/', views.TeamCompletedTask.as_view(), name='team_completed'),
    path('team/user/<int:pk>/stats', views.PerformanceDetail.as_view(), name = 'perf_detail'),
    path('team/<int:pk>/stats', views.PerformanceView.as_view(), name = 'perf_team'),
    path('team/<int:pk>/stats/page/<int:page>', views.PerformanceView.as_view(),
         name='perf_team_detail'),
   
    
    #######PROJECTS ######
    path('projects', views.ProjectsView.as_view(), name='projects'),
    path('projects/chart/<int:pk>', views.ChartDetail.as_view(), name='chart_detail'),
    path('projects/chart/create', views.ChartCreate.as_view(), name = "chart_create" ),
    path('projects/chart/load/<int:pk>', views.LoadChart, name="load_chart"),
    path('projects/chart/create/add_section/<int:pk>', views.AddSection.as_view(), name="add_section"),
    path('projects/chart/<int:pk>/create/task', views.ChartTaskCreate.as_view(),
          name='create_task_chart'),
    path('projects/chart/task/<int:pk>/update', views.ChartTaskUpdate.as_view(), name='chart_task_update'),
    path('projects/chart/<int:pk>/update', views.ChartUpdate.as_view(), name='chart_update'),
    path('projects/chart/sections/delete/<int:pk>', views.SectionDelete, name='sections_update'),
    path('projects/chart/<int:pk>/delete', views.ChartDelete.as_view(), name ='chart_delete'),
    path('projects/chart/<int:pk>/reset', views.ChartReset, name='reset_chart'),
    #path('projects/chart/save/<int:pk>', views.SaveChart, name='chart_save'),
    ######CHAT##########
    path('chat', views.ChatView.as_view(), name='chat_view'),
    path('chat/update', views.ChatUpdate, name='chat_update'),

] 