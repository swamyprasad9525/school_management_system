from django.db import models

class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., '2026-2027'
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one academic year is marked as current
            AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} {'(Current)' if self.is_current else ''}".strip()


class ClassGrade(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., 'Grade 10'
    numeric_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['numeric_order', 'name']

    def __str__(self):
        return self.name


class Section(models.Model):
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=20)  # e.g., 'Section A'
    class_teacher = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_sections'
    )

    class Meta:
        ordering = ['class_grade__numeric_order', 'name']
        constraints = [
            models.UniqueConstraint(fields=['class_grade', 'name'], name='unique_class_section')
        ]

    def __str__(self):
        return f"{self.class_grade.name} - {self.name}"


class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class ClassSubjectTeacher(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='class_assignments')
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, related_name='teaching_assignments')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['section', 'subject'], name='unique_section_subject_assignment')
        ]

    def __str__(self):
        return f"{self.section} | {self.subject.name} ({self.teacher})"


class StudentEnrollment(models.Model):
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='enrollments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='student_enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='student_enrollments')
    roll_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'academic_year'], name='unique_student_academic_year_enrollment')
        ]

    def __str__(self):
        return f"{self.student} -> {self.section} ({self.academic_year})"
