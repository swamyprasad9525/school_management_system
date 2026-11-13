from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from accounts.permissions import admin_required, role_required
from accounts.models import Role, StudentProfile, TeacherProfile
from .models import ClassGrade, Section, Subject, ClassSubjectTeacher, StudentEnrollment

@admin_required
def classes_list(request):
    classes = ClassGrade.objects.prefetch_related('sections__class_teacher__user').all()
    return render(request, 'academics/classes_list.html', {'classes': classes})

@admin_required
def subjects_list(request):
    subjects = Subject.objects.all()
    assignments = ClassSubjectTeacher.objects.select_related('section__class_grade', 'subject', 'teacher__user').all()
    return render(request, 'academics/subjects_list.html', {
        'subjects': subjects,
        'assignments': assignments,
    })

@admin_required
def teachers_list(request):
    teachers = TeacherProfile.objects.select_related('user').prefetch_related('assigned_sections__class_grade').all()
    return render(request, 'academics/teachers_list.html', {'teachers': teachers})

@role_required([Role.ADMIN, Role.TEACHER])
def students_list(request):
    """
    Lists students.
    Admin sees all students.
    Teacher sees students enrolled in their assigned sections/subjects.
    """
    search_query = request.GET.get('q', '')
    class_filter = request.GET.get('class', '')

    queryset = StudentEnrollment.objects.select_related(
        'student__user', 'student__guardian__user', 'section__class_grade', 'academic_year'
    ).filter(is_active=True)

    if request.user.is_teacher_role:
        teacher = request.user.teacher_profile
        # Find sections where teacher is class teacher or subject teacher
        teacher_sections = Section.objects.filter(class_teacher=teacher) | Section.objects.filter(subject_assignments__teacher=teacher)
        queryset = queryset.filter(section__in=teacher_sections.distinct())

    if class_filter:
        queryset = queryset.filter(section__class_grade_id=class_filter)
    if search_query:
        queryset = queryset.filter(
            student__user__first_name__icontains=search_query
        ) | queryset.filter(
            student__user__last_name__icontains=search_query
        ) | queryset.filter(
            student__admission_number__icontains=search_query
        )

    paginator = Paginator(queryset.distinct(), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    classes = ClassGrade.objects.all()

    return render(request, 'academics/students_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'class_filter': class_filter,
        'classes': classes,
    })

@role_required([Role.ADMIN, Role.TEACHER, Role.GUARDIAN, Role.STUDENT])
def student_detail(request, student_id):
    """
    Displays complete student profile, academic history, attendance rate, and fee balance.
    Enforces strict privacy:
    - Admin: Can view any student.
    - Teacher: Can only view if assigned to the student's class.
    - Guardian: Can ONLY view their linked child.
    - Student: Can ONLY view their own profile.
    """
    student = get_object_or_404(StudentProfile.objects.select_related('user', 'guardian__user'), id=student_id)

    # Privacy Enforcement
    user = request.user
    if user.is_guardian_role:
        if student.guardian != user.guardian_profile:
            messages.error(request, "Access Denied: You can only view your own children's records.")
            return redirect('core:guardian_dashboard')
    elif user.is_student_role:
        if student != user.student_profile:
            messages.error(request, "Access Denied: You can only view your own profile.")
            return redirect('core:guardian_dashboard')
    elif user.is_teacher_role:
        teacher = user.teacher_profile
        has_access = StudentEnrollment.objects.filter(
            student=student,
            is_active=True,
            section__in=Section.objects.filter(class_teacher=teacher) | Section.objects.filter(subject_assignments__teacher=teacher)
        ).exists()
        if not has_access and not user.is_superuser:
            messages.error(request, "Access Denied: You are not assigned to this student's class.")
            return redirect('academics:students_list')

    enrollment = student.enrollments.filter(is_active=True).first()

    return render(request, 'academics/student_detail.html', {
        'student': student,
        'enrollment': enrollment,
    })
