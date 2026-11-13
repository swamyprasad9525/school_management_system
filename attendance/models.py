from django.db import models

class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', 'Present'
    ABSENT = 'ABSENT', 'Absent'
    LATE = 'LATE', 'Late'
    EXCUSED = 'EXCUSED', 'Excused'

class AttendanceSession(models.Model):
    date = models.DateField()
    section = models.ForeignKey('academics.Section', on_delete=models.CASCADE, related_name='attendance_sessions')
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE, related_name='attendance_sessions')
    taken_by = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taken_attendance_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'section']
        constraints = [
            models.UniqueConstraint(fields=['date', 'section'], name='unique_date_section_session')
        ]

    def __str__(self):
        return f"{self.section} on {self.date}"

    @property
    def total_students(self):
        return self.records.count()

    @property
    def present_count(self):
        return self.records.filter(status=AttendanceStatus.PRESENT).count()

    @property
    def absent_count(self):
        return self.records.filter(status=AttendanceStatus.ABSENT).count()


class AttendanceRecord(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=15, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['student__user__first_name', 'student__user__last_name']
        constraints = [
            models.UniqueConstraint(fields=['session', 'student'], name='unique_student_session_attendance')
        ]

    def __str__(self):
        return f"{self.student} - {self.session.date}: {self.get_status_display()}"
