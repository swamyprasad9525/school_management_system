from django.contrib import admin
from .models import GradingScale, GradeRule, Exam, ExamSubject, ExamResult

class GradeRuleInline(admin.TabularInline):
    model = GradeRule
    extra = 1

@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [GradeRuleInline]

class ExamSubjectInline(admin.TabularInline):
    model = ExamSubject
    extra = 1

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'start_date', 'end_date', 'grading_scale', 'is_published')
    list_filter = ('academic_year', 'is_published')
    inlines = [ExamSubjectInline]

@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = ('exam', 'class_grade', 'subject', 'max_marks', 'pass_marks')
    list_filter = ('exam', 'class_grade')

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam_subject', 'marks_obtained', 'grade')
    list_filter = ('exam_subject__exam', 'exam_subject__class_grade', 'grade')
    search_fields = ('student__admission_number', 'student__user__first_name', 'student__user__last_name')
