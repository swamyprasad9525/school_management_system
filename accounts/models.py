from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin / Staff'
    TEACHER = 'TEACHER', 'Teacher'
    GUARDIAN = 'GUARDIAN', 'Guardian'
    STUDENT = 'STUDENT', 'Student'

class CustomUser(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)
    phone = models.CharField(max_length=20, blank=True)

    @property
    def is_admin_role(self):
        return self.role == Role.ADMIN or self.is_superuser

    @property
    def is_teacher_role(self):
        return self.role == Role.TEACHER

    @property
    def is_guardian_role(self):
        return self.role == Role.GUARDIAN

    @property
    def is_student_role(self):
        return self.role == Role.STUDENT

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=100, default='Teacher')
    qualification = models.CharField(max_length=150, blank=True)
    joining_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} [{self.employee_id}]"


class GuardianProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='guardian_profile')
    relationship = models.CharField(max_length=50, default='Parent')
    emergency_contact = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} (Guardian)"


class StudentProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    admission_number = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='M')
    guardian = models.ForeignKey(GuardianProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    roll_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.admission_number})"
