from django.contrib import admin
from .models import AttendanceSession, AttendanceRecord

class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'section', 'academic_year', 'taken_by', 'created_at')
    list_filter = ('date', 'section__class_grade', 'academic_year')
    inlines = [AttendanceRecordInline]

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status', 'remarks')
    list_filter = ('status', 'session__date', 'session__section__class_grade')
    search_fields = ('student__admission_number', 'student__user__first_name', 'student__user__last_name')
