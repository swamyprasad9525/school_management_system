from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('sessions/', views.sessions_list, name='sessions_list'),
    path('record/', views.record_attendance, name='record_attendance'),
    path('summary/', views.summary_report, name='summary_report'),
]

