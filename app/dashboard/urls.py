from . import views
from django.urls import path
from .forms import CustomPasswordChangeForm, ProfileUpdateForm


app_name = 'dashboard'
urlpatterns = [
    
    ####### Users , Home#########
    path('home/', views.BillboardView.as_view(), name = 'home'),
    path('logout/', views.LogoutView.as_view(), name ='logout'),
    path('report/', views.ReportView.as_view(), name='report'),
    path('role_dispatch/', views.role_dispatch, name='role_dispatch'),
    path('account/<int:pk>', views.AccountView.as_view(), name='user_account'),
    path('account/update/<int:pk>', views.AccountUpdate.as_view(form_class=ProfileUpdateForm),
     name='account_update'),
    path('account/update/password/<int:pk>', views.PasswordChangeView.as_view(
        form_class=CustomPasswordChangeForm), name="password_update"),
 
    ####### Messages ##########
    path('messages/reply/create/<int:recipient_id>', views.ReplyView.as_view(),
          name="message_reply"),
    path('messages/', views.HomeView.as_view(), name='messages'),
    path('messages/create/', views.MessageView.as_view(), name = 'messages_create'),
    path('messages/forward/<int:pk>', views.MessageForward.as_view(), name='message_forward'),
    path('report_detail/<int:id>/', views.MessageDetail.as_view(), name='reportview'),
    path('messages/inbox', views.InboxView.as_view(), name = 'inbox'),
    path('delete_report/<int:pk>', views.MessageDelete.as_view(), name = 'report_delete'),
    path('update_report/<int:pk>', views.MessageUpdate.as_view(), name = 'report_update'),
    ##########TASKS#########
    path('tasks/<int:pk>/activate', views.setActiveTask, name='activate_task'),
    path('tasks/subtask/<int:pk>', views.FetchSubtask, name='fetch_subtask'),
    path('tasks/<int:task>/subtask/<int:pk>', views.SubtaskCompleted, name="subtask_completed"),
    path('tasks/', views.TasksList.as_view(), name = 'tasks_list'),
    path('tasks/<int:pk>/', views.TaskDetail.as_view(), name='task_detail'),
    path('tasks/delete/<int:pk>', views.TaskDelete.as_view(), name = 'task_delete'),
    path('tasks/completed/<int:pk>', views.TaskSubmit.as_view(), name='task_submit'),
    ######### Files #########
    path('pic_picture/<int:pk>', views.stream_file, name='pic_picture'),
    path('pic_picture_completed_task/<int:pk>', views.stream_completed_task_img, 
         name='stream_completed_task_img'),
    path('file/<int:pk>/download', views.GetFile, name="get_file"),
    path('report/<int:pk>/download', views.getReport, name='get_report'),
    path('file/<int:pk>/task/delete/<int:manage>', views.DelFile, name='delete_file'),
    path('resource/<int:pk>', views.getResource, name='get_resource'),
    ####### MANAGE ###########
    path('team/', views.TeamView.as_view(), name = 'team'),
    path('tasks/completed/<int:pk>/', views.TaskCompletedDetail.as_view(), name='task_completed_detail'),
    path('tasks/create/', views.TaskManageCreate.as_view(), name = 'task_manage_create'),
    path('tasks/update/<int:pk>', views.TaskUpdate.as_view(), name = 'task_manage_update'),
    path('tasks/completed/approve/<int:pk>', views.TeamCompletedApprove.as_view(), 
         name = 'task_approve'),
    path('team/ressources', views.RessourcesView.as_view(), name="ressources"),
    path('team/getSection/<int:chart>', views.getSection, name='get_section'),



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


    ####### Milestones ########
  
    path('history/milestones', views.HistoryView.as_view(), name='history_view'),
    path('team/vs_team', views.TeamVs.as_view(), name="team_vs"),
    
    #######PROJECTS ######
    path('projects', views.ProjectsView.as_view(), name='projects'),
    path('projects/chart/<int:pk>', views.ChartDetail.as_view(), name='chart_detail'),
    path('projects/chart/create', views.ChartCreate.as_view(), name = "chart_create" ),
    path('projects/chart/load/<int:pk>', views.LoadChart, name="load_chart"),
    path('projects/chart/create/add_section/<int:pk>', views.AddSection.as_view(), name="add_section"),
    path('projects/chart/<int:pk>/create/task', views.ChartTaskCreate.as_view(),
          name='create_task_chart'),
    path('projects/chart/<int:chart>/task/<int:pk>/update', views.ChartTaskUpdate.as_view(), name='chart_task_update'),
    path('projects/chart/<int:pk>/update', views.ChartUpdate.as_view(), name='chart_update'),
    path('projects/chart/sections/delete/<int:pk>', views.SectionDelete, name='sections_update'),
    path('projects/chart/<int:pk>/delete', views.ChartDelete.as_view(), name ='chart_delete'),
    path('projects/chart/<int:pk>/reset', views.ChartReset, name='reset_chart'),
    #path('projects/chart/save/<int:pk>', views.SaveChart, name='chart_save'),
    path('projects/chart/<int:task_id>/<int:section_id>/<int:chart_id>/<str:prev>/<str:next>', 
         views.SwapTask, name='swapTask'),
    ######CHAT##########
    path('chat', views.ChatView.as_view(), name='chat_view'),
    path('chat/update', views.ChatUpdate, name='chat_update'),

] 