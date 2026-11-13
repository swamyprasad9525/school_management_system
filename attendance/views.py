from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from accounts.permissions import role_required, Role
from accounts.models import StudentProfile
from academics.models import Section, StudentEnrollment, AcademicYear
from audit.models import log_action
from .models import AttendanceSession, AttendanceRecord, AttendanceStatus

@role_required([Role.ADMIN, Role.TEACHER])
def sessions_list(request):
    sessions = AttendanceSession.objects.select_related('section__class_grade', 'academic_year', 'taken_by__user').all()

    if request.user.is_teacher_role and not request.user.is_superuser:
        teacher = request.user.teacher_profile
        # Teacher sees sessions for their assigned sections
        teacher_sections = Section.objects.filter(
            Q(class_teacher=teacher) | Q(subject_assignments__teacher=teacher)
        ).distinct()
        sessions = sessions.filter(section__in=teacher_sections)

    return render(request, 'attendance/sessions_list.html', {'sessions': sessions})

@role_required([Role.ADMIN, Role.TEACHER])
def record_attendance(request):
    """
    Records daily attendance for a selected section and date.
    Enforces Acceptance Criteria 1:
    Teacher can access ONLY assigned classes.
    """
    user = request.user
    selected_section_id = request.GET.get('section') or request.POST.get('section')
    attendance_date = request.GET.get('date') or request.POST.get('date') or str(timezone.now().date())

    # Build available sections based on role
    if user.is_admin_role or user.is_superuser:
        available_sections = Section.objects.select_related('class_grade').all()
    else:
        teacher = user.teacher_profile
        available_sections = Section.objects.filter(
            Q(class_teacher=teacher) | Q(subject_assignments__teacher=teacher)
        ).select_related('class_grade').distinct()

    section = None
    enrollments = []
    existing_records = {}

    if selected_section_id:
        # Enforce server-side authorization: Teacher can ONLY record for assigned sections
        if not user.is_admin_role and not user.is_superuser:
            if not available_sections.filter(id=selected_section_id).exists():
                raise PermissionDenied("Access Denied: You are not assigned to this class.")

        section = get_object_or_404(Section, id=selected_section_id)
        current_year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()

        enrollments = StudentEnrollment.objects.filter(
            section=section,
            is_active=True
        ).select_related('student__user').order_by('student__user__first_name', 'student__user__last_name')

        # Check if session already exists for this date and section
        session = AttendanceSession.objects.filter(date=attendance_date, section=section).first()
        if session:
            existing_records = {rec.student_id: rec.status for rec in session.records.all()}

        if request.method == 'POST':
            with transaction.atomic():
                # Upsert AttendanceSession
                teacher_profile = user.teacher_profile if hasattr(user, 'teacher_profile') else None
                session, _ = AttendanceSession.objects.update_or_create(
                    date=attendance_date,
                    section=section,
                    defaults={
                        'academic_year': current_year,
                        'taken_by': teacher_profile,
                    }
                )

                # Process records for each enrolled student
                updated_count = 0
                for enrollment in enrollments:
                    student_id = enrollment.student_id
                    status_val = request.POST.get(f'status_{student_id}', AttendanceStatus.PRESENT)
                    remarks_val = request.POST.get(f'remarks_{student_id}', '')

                    # UniqueConstraint guarantees safe upsert (Acceptance Test 2)
                    AttendanceRecord.objects.update_or_create(
                        session=session,
                        student=enrollment.student,
                        defaults={
                            'status': status_val,
                            'remarks': remarks_val,
                        }
                    )
                    updated_count += 1

                log_action(
                    actor=user,
                    action='ATTENDANCE',
                    model_name='AttendanceSession',
                    object_id=session.id,
                    object_repr=f"{section} on {attendance_date}",
                    details=f"Recorded attendance for {updated_count} students.",
                    ip_address=request.META.get('REMOTE_ADDR')
                )

                messages.success(request, f"Attendance for {section} on {attendance_date} recorded successfully ({updated_count} students).")
                return redirect('attendance:sessions_list')

    return render(request, 'attendance/record_attendance.html', {
        'available_sections': available_sections,
        'selected_section_id': selected_section_id,
        'attendance_date': attendance_date,
        'section': section,
        'enrollments': enrollments,
        'existing_records': existing_records,
        'status_choices': AttendanceStatus.choices,
    })

@role_required([Role.ADMIN, Role.TEACHER, Role.GUARDIAN, Role.STUDENT])
def summary_report(request):
    """
    Summary attendance rates by section and student.
    Guardians only see their linked children.
    """
    user = request.user
    if user.is_guardian_role:
        students = StudentProfile.objects.filter(guardian=user.guardian_profile)
    elif user.is_student_role:
        students = StudentProfile.objects.filter(user=user)
    else:
        students = StudentProfile.objects.all()

    student_stats = []
    for s in students:
        total = s.attendance_records.count()
        present = s.attendance_records.filter(status=AttendanceStatus.PRESENT).count()
        rate = round((present / total) * 100, 1) if total > 0 else 100.0
        student_stats.append({
            'student': s,
            'total': total,
            'present': present,
            'absent': s.attendance_records.filter(status=AttendanceStatus.ABSENT).count(),
            'rate': rate,
        })

    return render(request, 'attendance/summary_report.html', {
        'student_stats': student_stats,
    })
