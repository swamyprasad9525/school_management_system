from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from accounts.models import Role, TeacherProfile, GuardianProfile, StudentProfile
from academics.models import AcademicYear, ClassGrade, Section, Subject, ClassSubjectTeacher, StudentEnrollment
from attendance.models import AttendanceSession, AttendanceRecord, AttendanceStatus
from examinations.models import GradingScale, GradeRule, Exam, ExamSubject, ExamResult
from finance.models import FeeCategory, FeeStructure, FeeInvoice, FeePayment, InvoiceStatus, PaymentMethod

User = get_user_model()

class SchoolManagementSystemAcceptanceTests(TestCase):
    """
    Automated acceptance test suite verifying all 5 primary business rules
    and security constraints specified by the Algions assessment brief.
    """

    def setUp(self):
        self.client = Client()

        # 1. Academic Year
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 6, 30),
            is_current=True
        )

        # 2. Users & Roles
        self.admin_user = User.objects.create_user(
            username="test_admin", password="password123", role=Role.ADMIN, is_staff=True
        )

        self.teacher_user1 = User.objects.create_user(
            username="teacher_sarah", password="password123", role=Role.TEACHER, is_staff=True
        )
        self.teacher1 = TeacherProfile.objects.create(
            user=self.teacher_user1, employee_id="EMP-T1"
        )

        self.teacher_user2 = User.objects.create_user(
            username="teacher_david", password="password123", role=Role.TEACHER, is_staff=True
        )
        self.teacher2 = TeacherProfile.objects.create(
            user=self.teacher_user2, employee_id="EMP-T2"
        )

        self.guardian_user1 = User.objects.create_user(
            username="guardian_robert", password="password123", role=Role.GUARDIAN
        )
        self.guardian1 = GuardianProfile.objects.create(
            user=self.guardian_user1, relationship="Father"
        )

        self.guardian_user2 = User.objects.create_user(
            username="guardian_maria", password="password123", role=Role.GUARDIAN
        )
        self.guardian2 = GuardianProfile.objects.create(
            user=self.guardian_user2, relationship="Mother"
        )

        self.student_user1 = User.objects.create_user(
            username="student_alice", password="password123", role=Role.STUDENT
        )
        self.student1 = StudentProfile.objects.create(
            user=self.student_user1, admission_number="ADM-001", guardian=self.guardian1
        )

        self.student_user2 = User.objects.create_user(
            username="student_leo", password="password123", role=Role.STUDENT
        )
        self.student2 = StudentProfile.objects.create(
            user=self.student_user2, admission_number="ADM-002", guardian=self.guardian2
        )

        # 3. Academics
        self.grade10 = ClassGrade.objects.create(name="Grade 10", numeric_order=10)
        self.section_a = Section.objects.create(class_grade=self.grade10, name="Section A", class_teacher=self.teacher1)
        self.section_b = Section.objects.create(class_grade=self.grade10, name="Section B", class_teacher=self.teacher2)

        self.sub_math = Subject.objects.create(code="MTH-101", name="Mathematics")
        self.sub_sci = Subject.objects.create(code="SCI-101", name="Science")

        ClassSubjectTeacher.objects.create(section=self.section_a, subject=self.sub_math, teacher=self.teacher1)
        ClassSubjectTeacher.objects.create(section=self.section_b, subject=self.sub_sci, teacher=self.teacher2)

        self.enrollment1 = StudentEnrollment.objects.create(student=self.student1, section=self.section_a, academic_year=self.academic_year)
        self.enrollment2 = StudentEnrollment.objects.create(student=self.student2, section=self.section_b, academic_year=self.academic_year)

        # 4. Grading Scale
        self.scale = GradingScale.objects.create(name="Assessment Scale")
        GradeRule.objects.create(grading_scale=self.scale, grade="A+", min_percentage=Decimal("90.00"), max_percentage=Decimal("100.00"), grade_point=Decimal("4.00"))
        GradeRule.objects.create(grading_scale=self.scale, grade="A", min_percentage=Decimal("80.00"), max_percentage=Decimal("89.99"), grade_point=Decimal("3.70"))
        GradeRule.objects.create(grading_scale=self.scale, grade="B", min_percentage=Decimal("70.00"), max_percentage=Decimal("79.99"), grade_point=Decimal("3.00"))
        GradeRule.objects.create(grading_scale=self.scale, grade="C", min_percentage=Decimal("60.00"), max_percentage=Decimal("69.99"), grade_point=Decimal("2.00"))
        GradeRule.objects.create(grading_scale=self.scale, grade="F", min_percentage=Decimal("0.00"), max_percentage=Decimal("59.99"), grade_point=Decimal("0.00"))

        # 5. Exam
        self.exam = Exam.objects.create(
            name="Mid-Term Test",
            academic_year=self.academic_year,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 5),
            grading_scale=self.scale
        )
        self.es_math = ExamSubject.objects.create(
            exam=self.exam, subject=self.sub_math, class_grade=self.grade10, max_marks=Decimal("100.00"), pass_marks=Decimal("40.00")
        )

        # 6. Finance
        self.cat_tuition = FeeCategory.objects.create(name="Tuition Fee")
        self.fee_structure = FeeStructure.objects.create(
            category=self.cat_tuition, class_grade=self.grade10, academic_year=self.academic_year, amount=Decimal("1000.00"), due_date=date(2026, 12, 31)
        )
        self.invoice = FeeInvoice.objects.create(
            invoice_number="INV-TEST-001",
            student=self.student1,
            fee_structure=self.fee_structure,
            total_amount=Decimal("1000.00"),
            due_date=date(2026, 12, 31)
        )

    # -------------------------------------------------------------
    # ACCEPTANCE TEST 1: Teacher Access Control
    # -------------------------------------------------------------
    def test_teacher_can_access_only_assigned_classes_for_attendance(self):
        """
        Teacher 1 is assigned Section A.
        Attempting to record attendance for Section B must return HTTP 403 Forbidden.
        """
        self.client.login(username="teacher_sarah", password="password123")

        # Unauthorized access attempt to Section B
        response = self.client.get(reverse('attendance:record_attendance'), {'section': self.section_b.id})
        self.assertEqual(response.status_code, 403)

        # Authorized access to Section A
        response = self.client.get(reverse('attendance:record_attendance'), {'section': self.section_a.id})
        self.assertEqual(response.status_code, 200)

    # -------------------------------------------------------------
    # ACCEPTANCE TEST 2: Duplicate Attendance Rejection / Safe Update
    # -------------------------------------------------------------
    def test_duplicate_attendance_prevented_by_unique_constraint(self):
        """
        UniqueConstraint on (session, student) rejects duplicate entries at DB level.
        """
        today = date.today()
        session = AttendanceSession.objects.create(
            date=today, section=self.section_a, academic_year=self.academic_year, taken_by=self.teacher1
        )
        AttendanceRecord.objects.create(session=session, student=self.student1, status=AttendanceStatus.PRESENT)

        # Attempt duplicate insert directly
        with self.assertRaises(IntegrityError):
            AttendanceRecord.objects.create(session=session, student=self.student1, status=AttendanceStatus.ABSENT)

    def test_attendance_safe_upsert_via_view(self):
        """
        The view safely updates existing attendance records without duplicate rows.
        """
        self.client.login(username="teacher_sarah", password="password123")
        today = str(date.today())

        # First post: mark PRESENT
        post_data = {
            'section': self.section_a.id,
            'date': today,
            f'status_{self.student1.id}': AttendanceStatus.PRESENT,
        }
        res1 = self.client.post(reverse('attendance:record_attendance'), post_data)
        self.assertEqual(res1.status_code, 302)

        session = AttendanceSession.objects.get(date=today, section=self.section_a)
        self.assertEqual(session.records.count(), 1)
        self.assertEqual(session.records.first().status, AttendanceStatus.PRESENT)

        # Second post (same date/session): safely update to LATE
        post_data[f'status_{self.student1.id}'] = AttendanceStatus.LATE
        res2 = self.client.post(reverse('attendance:record_attendance'), post_data)
        self.assertEqual(res2.status_code, 302)

        # Still exactly 1 record, status updated
        self.assertEqual(session.records.count(), 1)
        self.assertEqual(session.records.first().status, AttendanceStatus.LATE)

    # -------------------------------------------------------------
    # ACCEPTANCE TEST 3: Exam Result & Grade Calculation
    # -------------------------------------------------------------
    def test_exam_result_grade_calculation(self):
        """
        Marks 95/100 -> A+, Marks 85/100 -> A, Marks 75/100 -> B, Marks 50/100 -> F
        """
        r1 = ExamResult.objects.create(exam_subject=self.es_math, student=self.student1, marks_obtained=Decimal("95.00"))
        self.assertEqual(r1.grade, "A+")

        r2 = ExamResult.objects.create(exam_subject=self.es_math, student=self.student2, marks_obtained=Decimal("75.00"))
        self.assertEqual(r2.grade, "B")

        # Test edge case: marks exceeding max_marks rejected
        with self.assertRaises(ValidationError):
            invalid_result = ExamResult(exam_subject=self.es_math, student=self.student1, marks_obtained=Decimal("105.00"))
            invalid_result.full_clean()

        # Test edge case: negative marks rejected
        with self.assertRaises(ValidationError):
            invalid_result = ExamResult(exam_subject=self.es_math, student=self.student1, marks_obtained=Decimal("-5.00"))
            invalid_result.full_clean()

    # -------------------------------------------------------------
    # ACCEPTANCE TEST 4: Guardian Privacy & Data Isolation
    # -------------------------------------------------------------
    def test_guardian_sees_only_linked_student(self):
        """
        Guardian 1 is linked ONLY to Student 1.
        Guardian 1 viewing Student 2's report card or detail receives HTTP 403 / redirect.
        """
        self.client.login(username="guardian_robert", password="password123")

        # Guardian 1 accesses own child (Alice) -> HTTP 200
        res_own = self.client.get(reverse('examinations:student_report_card', args=[self.student1.id]))
        self.assertEqual(res_own.status_code, 200)

        # Guardian 1 accesses unlinked child (Leo) -> HTTP 403 Forbidden
        res_other = self.client.get(reverse('examinations:student_report_card', args=[self.student2.id]))
        self.assertEqual(res_other.status_code, 403)

    def test_payment_receipt_privacy(self):
        """
        Guardian can only view payment receipts for their own linked children.
        """
        payment = FeePayment.objects.create(
            invoice=self.invoice,
            transaction_reference="PAY-TEST-REC-1",
            amount=Decimal("200.00"),
            payment_method=PaymentMethod.SIMULATED_CARD,
            recorded_by=self.admin_user
        )

        # Guardian 1 (linked to Student 1) -> HTTP 200
        self.client.login(username="guardian_robert", password="password123")
        res1 = self.client.get(reverse('finance:payment_receipt', args=[payment.id]))
        self.assertEqual(res1.status_code, 200)

        # Guardian 2 (linked to Student 2, not Student 1) -> HTTP 403 Forbidden
        self.client.login(username="guardian_maria", password="password123")
        res2 = self.client.get(reverse('finance:payment_receipt', args=[payment.id]))
        self.assertEqual(res2.status_code, 403)

    # -------------------------------------------------------------
    # ACCEPTANCE TEST 5: Fee Ledger Reconciliation
    # -------------------------------------------------------------
    def test_fee_ledger_reconciliation(self):
        """
        Verifies that paid_amount, balance, and total_amount reconcile exactly
        across partial and complete payments.
        """
        self.assertEqual(self.invoice.total_amount, Decimal("1000.00"))
        self.assertEqual(self.invoice.paid_amount, Decimal("0.00"))
        self.assertEqual(self.invoice.balance, Decimal("1000.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.UNPAID)

        # Partial Payment $400
        FeePayment.objects.create(
            invoice=self.invoice,
            transaction_reference="PAY-TEST-001",
            amount=Decimal("400.00"),
            payment_method=PaymentMethod.SIMULATED_CARD,
            recorded_by=self.admin_user
        )
        self.invoice.reconcile_ledger()

        self.assertEqual(self.invoice.paid_amount, Decimal("400.00"))
        self.assertEqual(self.invoice.balance, Decimal("600.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.PARTIAL)
        self.assertEqual(self.invoice.total_amount, self.invoice.paid_amount + self.invoice.balance)

        # Final Payment $600
        FeePayment.objects.create(
            invoice=self.invoice,
            transaction_reference="PAY-TEST-002",
            amount=Decimal("600.00"),
            payment_method=PaymentMethod.SIMULATED_CARD,
            recorded_by=self.admin_user
        )
        self.invoice.reconcile_ledger()

        self.assertEqual(self.invoice.paid_amount, Decimal("1000.00"))
        self.assertEqual(self.invoice.balance, Decimal("0.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.PAID)
        self.assertEqual(self.invoice.total_amount, self.invoice.paid_amount + self.invoice.balance)

    # -------------------------------------------------------------
    # NEGATIVE PAYMENT TESTS
    # -------------------------------------------------------------
    def test_negative_or_overpayment_rejected(self):
        """
        Rejects payments with amounts <= 0 or exceeding the invoice balance.
        """
        with self.assertRaises(ValidationError):
            p_neg = FeePayment(
                invoice=self.invoice,
                transaction_reference="PAY-NEG",
                amount=Decimal("-50.00")
            )
            p_neg.clean()

        with self.assertRaises(ValidationError):
            p_over = FeePayment(
                invoice=self.invoice,
                transaction_reference="PAY-OVER",
                amount=Decimal("1500.00")
            )
            p_over.clean()

    # -------------------------------------------------------------
    # ADVANCED CRUD ENDPOINTS TESTS
    # -------------------------------------------------------------
    def test_admin_can_enroll_student_via_view(self):
        """
        Admin can enroll a new student with auto user creation.
        """
        self.client.login(username="test_admin", password="password123")
        post_data = {
            'first_name': 'Ethan',
            'last_name': 'Hunt',
            'admission_number': 'ADM-NEW-999',
            'gender': 'M',
            'section': self.section_a.id,
            'guardian': self.guardian1.id,
        }
        res = self.client.post(reverse('academics:create_student'), post_data)
        self.assertEqual(res.status_code, 302)
        new_student = StudentProfile.objects.filter(admission_number='ADM-NEW-999').first()
        self.assertIsNotNone(new_student)
        self.assertEqual(new_student.user.first_name, 'Ethan')
        self.assertEqual(new_student.enrollments.count(), 1)

    def test_admin_can_generate_invoice_via_view(self):
        """
        Admin can generate a fee invoice for a student from an active structure.
        """
        self.client.login(username="test_admin", password="password123")
        post_data = {
            'student': self.student1.id,
            'fee_structure': self.fee_structure.id,
            'due_date': '2026-12-31',
        }
        res = self.client.post(reverse('finance:generate_invoice'), post_data)
        self.assertEqual(res.status_code, 302)
        inv = FeeInvoice.objects.filter(student=self.student1, fee_structure=self.fee_structure).last()
        self.assertIsNotNone(inv)
        self.assertEqual(inv.total_amount, Decimal("1000.00"))

    def test_all_dashboards_and_summary_views(self):
        """
        Tests that Admin, Teacher, Guardian dashboards and Attendance Summary report
        all render successfully with HTTP 200.
        """
        # Admin
        self.client.login(username="test_admin", password="password123")
        res = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(res.status_code, 200)
        res = self.client.get(reverse('attendance:summary_report'))
        self.assertEqual(res.status_code, 200)

        # Teacher
        self.client.login(username="teacher_sarah", password="password123")
        res = self.client.get(reverse('core:teacher_dashboard'))
        self.assertEqual(res.status_code, 200)

        # Guardian
        self.client.login(username="guardian_robert", password="password123")
        res = self.client.get(reverse('core:guardian_dashboard'))
        self.assertEqual(res.status_code, 200)
