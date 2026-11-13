from django.urls import path
from . import views

app_name = 'examinations'

urlpatterns = [
    path('exams/', views.exams_list, name='exams_list'),
    path('grading-scales/', views.grading_scales, name='grading_scales'),
    path('marks-entry/', views.teacher_marks_entry, name='teacher_marks_entry'),
    path('report-card/<int:student_id>/', views.student_report_card, name='student_report_card'),
]

