from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('classes/', views.classes_list, name='classes_list'),
    path('subjects/', views.subjects_list, name='subjects_list'),
    path('teachers/', views.teachers_list, name='teachers_list'),
    path('students/', views.students_list, name='students_list'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
]

