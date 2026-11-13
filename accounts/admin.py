from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, TeacherProfile, GuardianProfile, StudentProfile

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Contact', {'fields': ('role', 'phone')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'designation', 'joining_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')

@admin.register(GuardianProfile)
class GuardianProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'relationship', 'emergency_contact')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'admission_number', 'roll_number', 'guardian', 'gender')
    list_filter = ('gender',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'admission_number')
