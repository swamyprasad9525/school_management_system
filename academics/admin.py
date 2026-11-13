from django.contrib import admin
from .models import AcademicYear, ClassGrade, Section, Subject, ClassSubjectTeacher, StudentEnrollment

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')

@admin.register(ClassGrade)
class ClassGradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'numeric_order')

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('class_grade', 'name', 'class_teacher')
    list_filter = ('class_grade',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(ClassSubjectTeacher)
class ClassSubjectTeacherAdmin(admin.ModelAdmin):
    list_display = ('section', 'subject', 'teacher')
    list_filter = ('section__class_grade', 'teacher')

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'section', 'academic_year', 'roll_number', 'is_active')
    list_filter = ('academic_year', 'section__class_grade', 'is_active')
    search_fields = ('student__admission_number', 'student__user__first_name', 'student__user__last_name')
