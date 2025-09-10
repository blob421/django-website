from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path, include
from	rest_framework.routers import	DefaultRouter
from api.views import MessageViewSet, TaskViewSet,TeamViewSet, UserProfileViewSet

router = DefaultRouter()
router.register("messages", MessageViewSet)
router.register('tasks', TaskViewSet)
router.register('team', TeamViewSet)


urlpatterns = [

     path("jwt/", TokenObtainPairView.as_view(), name="jwt_obtain_pair"),
     path("jwt/refresh/", TokenRefreshView.as_view(), name="jwt_refresh"),
     path('checkAuth/', views.checkAuth.as_view({'get': 'get'}), name='checkAuth'),
     path("home/", views.Homeview.as_view({'get': 'retrieve'}), name="home"),
     path('upload/', views.ImageUploadView.as_view(), name='upload'),
     path('loading/<str:celery_id>/', views.Ready, name='ready'),
    # path('messages/unread', views.UnreadMessages.as_view(), name='unread_count'),
     path('profile/', views.UserProfileViewSet.as_view({'get':'retrieve'})),
     path("",	include(router.urls)),

     #path('home')
]