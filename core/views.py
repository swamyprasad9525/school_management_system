from decimal import Decimal
from django.shortcuts import render, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from accounts.permissions import admin_required, teacher_required, guardian_or_student_required, Role
from accounts.models import CustomUser, TeacherProfile, GuardianProfile, StudentProfile
from academics.models import ClassGrade, Section, Subject, StudentEnrollment, ClassSubjectTeacher
from attendance.models import AttendanceSession, AttendanceRecord, AttendanceStatus
from examinations.models import Exam, ExamResult
from finance.models import FeeInvoice, FeePayment, InvoiceStatus
from audit.models import AuditLog

def home(request):
    """
    Public landing page.
    If authenticated, redirects to user's role-specific dashboard.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    return render(request, 'core/home.html')

@admin_required
def admin_dashboard(request):
    """
    Operational command center for administrators.
    """
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    total_classes = ClassGrade.objects.count()

    # Attendance stats for today
    today = timezone.now().date()
    today_sessions = AttendanceSession.objects.filter(date=today)
    total_records = AttendanceRecord.objects.filter(session__date=today).count()
    present_records = AttendanceRecord.objects.filter(session__date=today, status=AttendanceStatus.PRESENT).count()
    today_attendance_rate = round((present_records / total_records) * 100, 1) if total_records > 0 else 0

    # Financial overview
    invoices = FeeInvoice.objects.all()
    total_invoiced = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_collected = invoices.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00')
    outstanding_fees = total_invoiced - total_collected
    collection_rate = round((total_collected / total_invoiced) * 100, 1) if total_invoiced > 0 else 0

    paid_invoices_count = invoices.filter(status=InvoiceStatus.PAID).count()
    partial_invoices_count = invoices.filter(status=InvoiceStatus.PARTIAL).count()
    unpaid_invoices_count = invoices.filter(status=InvoiceStatus.UNPAID).count()

    # Academic Grade Distribution
    grade_distribution = list(ExamResult.objects.values('grade').annotate(count=Count('id')).order_by('grade'))

    # Recent Audit Logs & Payments
    recent_logs = AuditLog.objects.select_related('actor').all()[:8]
    recent_payments = FeePayment.objects.select_related('invoice__student__user', 'recorded_by').all()[:5]

    return render(request, 'core/admin_dashboard.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'today_attendance_rate': today_attendance_rate,
        'today_sessions_count': today_sessions.count(),
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'outstanding_fees': outstanding_fees,
        'collection_rate': collection_rate,
        'paid_invoices_count': paid_invoices_count,
        'partial_invoices_count': partial_invoices_count,
        'unpaid_invoices_count': unpaid_invoices_count,
        'grade_distribution': grade_distribution,
        'recent_logs': recent_logs,
        'recent_payments': recent_payments,
    })

@teacher_required
def teacher_dashboard(request):
    """
    Dedicated workspace for faculty members.
    Shows assigned classes, assigned subjects, and quick actions.
    """
    teacher = request.user.teacher_profile

    # Assigned sections as Class Teacher
    class_sections = Section.objects.filter(class_teacher=teacher).select_related('class_grade')

    # Subject assignments
    subject_assignments = ClassSubjectTeacher.objects.filter(teacher=teacher).select_related('section__class_grade', 'subject')

    # Today's attendance status for assigned sections
    today = timezone.now().date()
    attendance_status_list = []
    for s in class_sections:
        session = AttendanceSession.objects.filter(section=s, date=today).first()
        attendance_status_list.append({
            'section': s,
            'is_recorded': session is not None,
            'session': session,
        })

    active_exams = Exam.objects.filter(is_published=True)[:3]

    return render(request, 'core/teacher_dashboard.html', {
        'teacher': teacher,
        'class_sections': class_sections,
        'subject_assignments': subject_assignments,
        'attendance_status_list': attendance_status_list,
        'active_exams': active_exams,
        'today': today,
    })

@guardian_or_student_required
def guardian_dashboard(request):
    """
    Dedicated parent & student portal.
    Enforces strict privacy: Guardian sees ONLY their linked children!
    """
    user = request.user
    if user.is_guardian_role:
        guardian = user.guardian_profile
        students = StudentProfile.objects.filter(guardian=guardian).select_related('user')
    else:
        students = StudentProfile.objects.filter(user=user).select_related('user')

    children_data = []
    for student in students:
        enrollment = student.enrollments.filter(is_active=True).first()

        # Attendance calculation
        total_att = student.attendance_records.count()
        present_att = student.attendance_records.filter(status=AttendanceStatus.PRESENT).count()
        att_rate = round((present_att / total_att) * 100, 1) if total_att > 0 else 100.0

        # Latest exam results
        latest_results = ExamResult.objects.filter(student=student).select_related('exam_subject__exam', 'exam_subject__subject')[:5]

        # Invoices and outstanding balance
        invoices = FeeInvoice.objects.filter(student=student)
        total_due = sum(inv.balance for inv in invoices)

        children_data.append({
            'student': student,
            'enrollment': enrollment,
            'attendance_rate': att_rate,
            'total_attendance': total_att,
            'present_attendance': present_att,
            'latest_results': latest_results,
            'invoices': invoices,
            'total_due': total_due,
        })

    return render(request, 'core/guardian_dashboard.html', {
        'children_data': children_data,
    })
