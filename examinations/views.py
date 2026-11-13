from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum, Q
from accounts.permissions import role_required, Role
from accounts.models import StudentProfile
from academics.models import ClassGrade, Section, Subject, StudentEnrollment, ClassSubjectTeacher
from audit.models import log_action
from .models import Exam, ExamSubject, ExamResult, GradingScale, GradeRule

@role_required([Role.ADMIN, Role.TEACHER])
def exams_list(request):
    exams = Exam.objects.select_related('academic_year', 'grading_scale').prefetch_related('exam_subjects__subject', 'exam_subjects__class_grade').all()
    return render(request, 'examinations/exams_list.html', {'exams': exams})

@role_required([Role.ADMIN])
def grading_scales(request):
    scales = GradingScale.objects.prefetch_related('rules').all()
    return render(request, 'examinations/grading_scales.html', {'scales': scales})

@role_required([Role.ADMIN, Role.TEACHER])
def teacher_marks_entry(request):
    """
    Teacher marks entry view.
    Enforces authorization:
    - Teacher can enter marks ONLY for their assigned subjects & classes.
    """
    user = request.user
    selected_exam_id = request.GET.get('exam') or request.POST.get('exam')
    selected_section_id = request.GET.get('section') or request.POST.get('section')
    selected_subject_id = request.GET.get('subject') or request.POST.get('subject')

    exams = Exam.objects.filter(is_published=True)

    if user.is_admin_role or user.is_superuser:
        sections = Section.objects.select_related('class_grade').all()
        subjects = Subject.objects.all()
    else:
        teacher = user.teacher_profile
        # Find sections and subjects assigned to this teacher
        assignments = ClassSubjectTeacher.objects.filter(teacher=teacher).select_related('section__class_grade', 'subject')
        sections = Section.objects.filter(id__in=assignments.values_list('section_id', flat=True)).select_related('class_grade')
        subjects = Subject.objects.filter(id__in=assignments.values_list('subject_id', flat=True))

    exam = None
    section = None
    subject = None
    exam_subject = None
    enrollments = []
    existing_results = {}

    if selected_exam_id and selected_section_id and selected_subject_id:
        exam = get_object_or_404(Exam, id=selected_exam_id)
        section = get_object_or_404(Section, id=selected_section_id)
        subject = get_object_or_404(Subject, id=selected_subject_id)

        # Server-side validation for teacher role
        if not user.is_admin_role and not user.is_superuser:
            is_assigned = ClassSubjectTeacher.objects.filter(
                teacher=user.teacher_profile,
                section=section,
                subject=subject
            ).exists()
            if not is_assigned:
                raise PermissionDenied("Access Denied: You are not assigned to teach this subject to this section.")

        exam_subject = ExamSubject.objects.filter(
            exam=exam,
            subject=subject,
            class_grade=section.class_grade
        ).first()

        if not exam_subject:
            messages.error(request, f"This subject ({subject.name}) is not scheduled for {exam.name} under Grade {section.class_grade.name}.")
        else:
            enrollments = StudentEnrollment.objects.filter(
                section=section,
                is_active=True
            ).select_related('student__user').order_by('student__user__first_name', 'student__user__last_name')

            results = ExamResult.objects.filter(exam_subject=exam_subject, student__in=[e.student for e in enrollments])
            existing_results = {r.student_id: r for r in results}

            if request.method == 'POST':
                with transaction.atomic():
                    saved_count = 0
                    has_error = False

                    for enrollment in enrollments:
                        student = enrollment.student
                        marks_val = request.POST.get(f'marks_{student.id}', '').strip()
                        remarks_val = request.POST.get(f'remarks_{student.id}', '').strip()

                        if marks_val != '':
                            try:
                                marks_decimal = Decimal(marks_val)
                                if marks_decimal < 0 or marks_decimal > exam_subject.max_marks:
                                    messages.error(
                                        request,
                                        f"Invalid marks for {student}: {marks_decimal}. Must be between 0 and {exam_subject.max_marks}."
                                    )
                                    has_error = True
                                    break

                                # Automatically calculate grade using exam's grading scale
                                percentage = (marks_decimal / exam_subject.max_marks) * 100
                                calc_grade = exam.grading_scale.get_grade_for_percentage(percentage) if exam.grading_scale else ('Pass' if marks_decimal >= exam_subject.pass_marks else 'Fail')

                                # Update or create (Acceptance Test 3)
                                ExamResult.objects.update_or_create(
                                    exam_subject=exam_subject,
                                    student=student,
                                    defaults={
                                        'marks_obtained': marks_decimal,
                                        'grade': calc_grade,
                                        'remarks': remarks_val,
                                    }
                                )
                                saved_count += 1
                            except (ValueError, TypeError, ValidationError) as e:
                                messages.error(request, f"Invalid marks format for {student}: {e}")
                                has_error = True
                                break

                    if not has_error and saved_count > 0:
                        log_action(
                            actor=user,
                            action='MARKS_ENTRY',
                            model_name='ExamResult',
                            object_id=exam_subject.id,
                            object_repr=f"{exam.name} - {subject.name} ({section})",
                            details=f"Saved marks for {saved_count} students.",
                            ip_address=request.META.get('REMOTE_ADDR')
                        )
                        messages.success(request, f"Successfully recorded and calculated marks for {saved_count} students.")
                        return redirect(f"{request.path}?exam={selected_exam_id}&section={selected_section_id}&subject={selected_subject_id}")

    return render(request, 'examinations/teacher_marks_entry.html', {
        'exams': exams,
        'sections': sections,
        'subjects': subjects,
        'selected_exam_id': selected_exam_id,
        'selected_section_id': selected_section_id,
        'selected_subject_id': selected_subject_id,
        'exam': exam,
        'section': section,
        'subject': subject,
        'exam_subject': exam_subject,
        'enrollments': enrollments,
        'existing_results': existing_results,
    })

@role_required([Role.ADMIN, Role.TEACHER, Role.GUARDIAN, Role.STUDENT])
def student_report_card(request, student_id):
    """
    Renders comprehensive student report card.
    Strict privacy:
    - Guardian can ONLY view linked student.
    - Student can ONLY view own.
    """
    student = get_object_or_404(StudentProfile.objects.select_related('user', 'guardian__user'), id=student_id)

    user = request.user
    if user.is_guardian_role:
        if student.guardian != user.guardian_profile:
            raise PermissionDenied("Access Denied: You cannot view report cards for other students.")
    elif user.is_student_role:
        if student != user.student_profile:
            raise PermissionDenied("Access Denied: You cannot view another student's report card.")

    enrollment = student.enrollments.filter(is_active=True).first()
    selected_exam_id = request.GET.get('exam')

    available_exams = Exam.objects.filter(is_published=True)
    if selected_exam_id:
        active_exam = available_exams.filter(id=selected_exam_id).first()
    else:
        active_exam = available_exams.first()

    results = []
    total_obtained = Decimal('0.00')
    total_max = Decimal('0.00')
    overall_percentage = Decimal('0.00')
    overall_grade = 'N/A'

    if active_exam:
        results = ExamResult.objects.filter(
            student=student,
            exam_subject__exam=active_exam
        ).select_related('exam_subject__subject', 'exam_subject__class_grade')

        for r in results:
            total_obtained += r.marks_obtained
            total_max += r.exam_subject.max_marks

        if total_max > 0:
            overall_percentage = round((total_obtained / total_max) * 100, 2)
            if active_exam.grading_scale:
                overall_grade = active_exam.grading_scale.get_grade_for_percentage(overall_percentage)
            else:
                overall_grade = 'Pass' if overall_percentage >= 40 else 'Fail'

    # Attendance summary for student
    total_attendance = student.attendance_records.count()
    present_attendance = student.attendance_records.filter(status='PRESENT').count()
    attendance_rate = round((present_attendance / total_attendance) * 100, 1) if total_attendance > 0 else 100.0

    return render(request, 'examinations/student_report_card.html', {
        'student': student,
        'enrollment': enrollment,
        'available_exams': available_exams,
        'active_exam': active_exam,
        'results': results,
        'total_obtained': total_obtained,
        'total_max': total_max,
        'overall_percentage': overall_percentage,
        'overall_grade': overall_grade,
        'attendance_rate': attendance_rate,
        'total_attendance': total_attendance,
        'present_attendance': present_attendance,
    })
