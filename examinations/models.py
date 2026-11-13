from django.db import models
from django.core.exceptions import ValidationError

class GradingScale(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def get_grade_for_percentage(self, percentage):
        """
        Calculates letter grade and grade point based on configured rules.
        """
        for rule in self.rules.all():
            if rule.min_percentage <= percentage <= rule.max_percentage:
                return rule.grade
        return 'F'


class GradeRule(models.Model):
    grading_scale = models.ForeignKey(GradingScale, on_delete=models.CASCADE, related_name='rules')
    grade = models.CharField(max_length=10)  # e.g., 'A+', 'A', 'B', 'C', 'F'
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    remarks = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-min_percentage']
        constraints = [
            models.UniqueConstraint(fields=['grading_scale', 'grade'], name='unique_scale_grade')
        ]

    def __str__(self):
        return f"{self.grade} ({self.min_percentage}% - {self.max_percentage}%)"


class Exam(models.Model):
    name = models.CharField(max_length=100)
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE, related_name='exams')
    start_date = models.DateField()
    end_date = models.DateField()
    grading_scale = models.ForeignKey(GradingScale, on_delete=models.SET_NULL, null=True, blank=True, related_name='exams')
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"


class ExamSubject(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_subjects')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='exam_subjects')
    class_grade = models.ForeignKey('academics.ClassGrade', on_delete=models.CASCADE, related_name='exam_subjects')
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    pass_marks = models.DecimalField(max_digits=5, decimal_places=2, default=40.0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['exam', 'subject', 'class_grade'], name='unique_exam_subject_grade')
        ]

    def __str__(self):
        return f"{self.exam.name} - {self.class_grade.name}: {self.subject.name} (Max: {self.max_marks})"


class ExamResult(models.Model):
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='exam_results')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=10, blank=True)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['exam_subject', 'student'], name='unique_student_exam_subject_result')
        ]

    def clean(self):
        if self.marks_obtained < 0:
            raise ValidationError("Marks obtained cannot be negative.")
        if self.marks_obtained > self.exam_subject.max_marks:
            raise ValidationError(f"Marks obtained ({self.marks_obtained}) cannot exceed maximum marks ({self.exam_subject.max_marks}).")

    def save(self, *args, **kwargs):
        self.clean()
        # Automatically determine grade from Exam's grading scale
        if not self.grade:
            exam = self.exam_subject.exam
            if exam.grading_scale and self.exam_subject.max_marks > 0:
                percentage = (self.marks_obtained / self.exam_subject.max_marks) * 100
                self.grade = exam.grading_scale.get_grade_for_percentage(percentage)
            else:
                self.grade = 'Pass' if self.marks_obtained >= self.exam_subject.pass_marks else 'Fail'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.exam_subject.subject.name}: {self.marks_obtained}/{self.exam_subject.max_marks} ({self.grade})"
