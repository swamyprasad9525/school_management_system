from rest_framework import serializers, viewsets, permissions
from accounts.models import CustomUser, StudentProfile, TeacherProfile
from academics.models import ClassGrade, Section, Subject, StudentEnrollment
from attendance.models import AttendanceSession, AttendanceRecord
from examinations.models import Exam, ExamSubject, ExamResult
from finance.models import FeeInvoice, FeePayment

# Serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role']

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = StudentProfile
        fields = ['id', 'admission_number', 'user', 'gender', 'date_of_birth']

class SectionSerializer(serializers.ModelSerializer):
    class_grade_name = serializers.CharField(source='class_grade.name', read_only=True)
    class Meta:
        model = Section
        fields = ['id', 'name', 'class_grade_name']

class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'student', 'student_name', 'admission_number', 'status', 'remarks']

class AttendanceSessionSerializer(serializers.ModelSerializer):
    records = AttendanceRecordSerializer(many=True, read_only=True)
    section_name = serializers.CharField(source='section.__str__', read_only=True)
    total_students = serializers.IntegerField(read_only=True)
    present_count = serializers.IntegerField(read_only=True)
    absent_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = AttendanceSession
        fields = ['id', 'date', 'section', 'section_name', 'total_students', 'present_count', 'absent_count', 'records']

class ExamResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='exam_subject.subject.name', read_only=True)
    exam_name = serializers.CharField(source='exam_subject.exam.name', read_only=True)
    class Meta:
        model = ExamResult
        fields = ['id', 'student', 'student_name', 'exam_name', 'subject_name', 'marks_obtained', 'grade', 'remarks']

class FeeInvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    fee_category = serializers.CharField(source='fee_structure.category.name', read_only=True)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = FeeInvoice
        fields = ['id', 'invoice_number', 'student', 'student_name', 'fee_category', 'total_amount', 'paid_amount', 'balance', 'status', 'due_date']


# ViewSets
class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to retrieve enrolled students.
    """
    queryset = StudentProfile.objects.select_related('user', 'guardian__user').all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class AttendanceSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to retrieve attendance sessions.
    """
    queryset = AttendanceSession.objects.prefetch_related('records__student__user').all()
    serializer_class = AttendanceSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

class ExamResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to retrieve exam marks.
    """
    queryset = ExamResult.objects.select_related('student__user', 'exam_subject__subject', 'exam_subject__exam').all()
    serializer_class = ExamResultSerializer
    permission_classes = [permissions.IsAuthenticated]

class FeeInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to retrieve student fee invoices.
    """
    queryset = FeeInvoice.objects.select_related('student__user', 'fee_structure__category').all()
    serializer_class = FeeInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
