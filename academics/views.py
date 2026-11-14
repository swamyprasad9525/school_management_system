from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import transaction
from accounts.permissions import admin_required, role_required
from accounts.models import Role, CustomUser, StudentProfile, TeacherProfile, GuardianProfile
from audit.models import log_action
from .models import ClassGrade, Section, Subject, ClassSubjectTeacher, StudentEnrollment, AcademicYear

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

    paginator = Paginator(queryset.distinct().order_by('section__class_grade__name', 'section__name', 'roll_number', 'student__admission_number'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    classes = ClassGrade.objects.all()
    all_sections = Section.objects.select_related('class_grade').all()
    all_guardians = GuardianProfile.objects.select_related('user').all()

    return render(request, 'academics/students_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'class_filter': class_filter,
        'classes': classes,
        'all_sections': all_sections,
        'all_guardians': all_guardians,
    })

@admin_required
def create_student(request):
    """
    Direct student enrollment endpoint from modal form.
    """
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        admission_no = request.POST.get('admission_number', '').strip()
        gender = request.POST.get('gender', 'M')
        section_id = request.POST.get('section')
        guardian_id = request.POST.get('guardian')

        if not (first_name and last_name and admission_no and section_id):
            messages.error(request, "Please fill in all required student enrollment fields.")
            return redirect('academics:students_list')

        if StudentProfile.objects.filter(admission_number=admission_no).exists():
            messages.error(request, f"Admission number '{admission_no}' already exists in the registry.")
            return redirect('academics:students_list')

        username = admission_no.lower().replace('-', '_')
        current_year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
        section = get_object_or_404(Section, id=section_id)
        guardian = GuardianProfile.objects.filter(id=guardian_id).first() if guardian_id else None

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                role=Role.STUDENT,
                email=f"{username}@student.algions.edu"
            )
            user.set_password("student123")
            user.save()

            student = StudentProfile.objects.create(
                user=user,
                admission_number=admission_no,
                gender=gender,
                guardian=guardian
            )

            StudentEnrollment.objects.create(
                student=student,
                section=section,
                academic_year=current_year,
                roll_number=str(section.student_enrollments.count() + 1)
            )

            log_action(
                actor=request.user,
                action='CREATE',
                model_name='StudentProfile',
                object_id=student.id,
                object_repr=f"{first_name} {last_name} ({admission_no})",
                details=f"Enrolled into {section}. Default password: student123",
                ip_address=request.META.get('REMOTE_ADDR')
            )

        messages.success(request, f"Student {first_name} {last_name} enrolled successfully in {section}!")
    return redirect('academics:students_list')

@role_required([Role.ADMIN, Role.TEACHER, Role.GUARDIAN, Role.STUDENT])
def student_detail(request, student_id):
    student = get_object_or_404(StudentProfile.objects.select_related('user', 'guardian__user'), id=student_id)

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
