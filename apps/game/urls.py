from django.urls import path

from . import views

app_name = 'game'

urlpatterns = [
    path('host/new/', views.host_new_session, name='host_new_session'),
    path('host/<str:code>/', views.host_session, name='host_session'),
    path('host/<str:code>/qr.png', views.host_qr, name='host_qr'),
]
