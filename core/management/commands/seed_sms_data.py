from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from accounts.models import Role, TeacherProfile, GuardianProfile, StudentProfile
from academics.models import AcademicYear, ClassGrade, Section, Subject, ClassSubjectTeacher, StudentEnrollment
from attendance.models import AttendanceSession, AttendanceRecord, AttendanceStatus
from examinations.models import GradingScale, GradeRule, Exam, ExamSubject, ExamResult
from finance.models import FeeCategory, FeeStructure, FeeInvoice, FeePayment, InvoiceStatus, PaymentMethod
from audit.models import AuditLog, log_action

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds the database with realistic synthetic data for Algions SMS assessment"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting SMS database seeding..."))

        with transaction.atomic():
            # 1. Academic Year
            academic_year, _ = AcademicYear.objects.get_or_create(
                name="2026-2027",
                defaults={
                    "start_date": date(2026, 8, 1),
                    "end_date": date(2027, 6, 30),
                    "is_current": True,
                }
            )

            # 2. Users & Roles
            # Admin User
            admin_user, _ = User.objects.get_or_create(
                username="admin",
                defaults={
                    "email": "admin@algions.edu",
                    "first_name": "Arthur",
                    "last_name": "Pendleton",
                    "role": Role.ADMIN,
                    "is_staff": True,
                    "is_superuser": True,
                }
            )
            admin_user.set_password("admin123")
            admin_user.save()

            # Teachers
            teacher_data = [
                ("teacher1", "Sarah", "Jenkins", "EMP-1001", "Senior Math Teacher", "M.Sc Mathematics"),
                ("teacher2", "David", "Kumar", "EMP-1002", "Science Department Head", "Ph.D Physics"),
                ("teacher3", "Elena", "Vance", "EMP-1003", "English Instructor", "M.A English Literature"),
            ]
            teachers = []
            for username, fname, lname, empid, desig, qual in teacher_data:
                u, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": f"{username}@algions.edu",
                        "first_name": fname,
                        "last_name": lname,
                        "role": Role.TEACHER,
                        "is_staff": True,
                    }
                )
                u.set_password("teacher123")
                u.save()
                tp, _ = TeacherProfile.objects.get_or_create(
                    user=u,
                    defaults={
                        "employee_id": empid,
                        "designation": desig,
                        "qualification": qual,
                    }
                )
                teachers.append(tp)

            # Guardians
            guardian_data = [
                ("guardian1", "Robert", "Taylor", "Father", "+1 555-0101", "742 Evergreen Terrace"),
                ("guardian2", "Maria", "Garcia", "Mother", "+1 555-0202", "123 Elm Street"),
            ]
            guardians = []
            for username, fname, lname, rel, phone, addr in guardian_data:
                u, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": f"{username}@example.com",
                        "first_name": fname,
                        "last_name": lname,
                        "role": Role.GUARDIAN,
                    }
                )
                u.set_password("guardian123")
                u.save()
                gp, _ = GuardianProfile.objects.get_or_create(
                    user=u,
                    defaults={
                        "relationship": rel,
                        "emergency_contact": phone,
                        "address": addr,
                    }
                )
                guardians.append(gp)

            # Students
            student_data = [
                ("student1", "Alice", "Taylor", "ADM-2026-001", "M", guardians[0], date(2011, 4, 15)),
                ("student2", "Leo", "Garcia", "ADM-2026-002", "M", guardians[1], date(2011, 8, 22)),
                ("student3", "Sofia", "Garcia", "ADM-2026-003", "F", guardians[1], date(2012, 11, 5)),
                ("student4", "Marcus", "Chen", "ADM-2026-004", "M", None, date(2011, 1, 30)),
            ]
            students = []
            for username, fname, lname, adm_no, gender, guardian, dob in student_data:
                u, _ = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": f"{username}@student.algions.edu",
                        "first_name": fname,
                        "last_name": lname,
                        "role": Role.STUDENT,
                    }
                )
                u.set_password("student123")
                u.save()
                sp, _ = StudentProfile.objects.get_or_create(
                    user=u,
                    defaults={
                        "admission_number": adm_no,
                        "gender": gender,
                        "guardian": guardian,
                        "date_of_birth": dob,
                    }
                )
                students.append(sp)

            # 3. Classes & Sections
            grade10, _ = ClassGrade.objects.get_or_create(name="Grade 10", defaults={"numeric_order": 10})
            grade9, _ = ClassGrade.objects.get_or_create(name="Grade 9", defaults={"numeric_order": 9})

            section_10a, _ = Section.objects.get_or_create(
                class_grade=grade10,
                name="Section A",
                defaults={"class_teacher": teachers[0]}
            )
            section_10b, _ = Section.objects.get_or_create(
                class_grade=grade10,
                name="Section B",
                defaults={"class_teacher": teachers[1]}
            )

            # 4. Subjects & Teacher Assignments
            sub_math, _ = Subject.objects.get_or_create(code="MATH-101", defaults={"name": "Advanced Mathematics"})
            sub_sci, _ = Subject.objects.get_or_create(code="SCI-101", defaults={"name": "Physics & Chemistry"})
            sub_eng, _ = Subject.objects.get_or_create(code="ENG-101", defaults={"name": "English Literature"})

            ClassSubjectTeacher.objects.get_or_create(section=section_10a, subject=sub_math, defaults={"teacher": teachers[0]})
            ClassSubjectTeacher.objects.get_or_create(section=section_10a, subject=sub_sci, defaults={"teacher": teachers[1]})
            ClassSubjectTeacher.objects.get_or_create(section=section_10a, subject=sub_eng, defaults={"teacher": teachers[2]})

            ClassSubjectTeacher.objects.get_or_create(section=section_10b, subject=sub_math, defaults={"teacher": teachers[0]})
            ClassSubjectTeacher.objects.get_or_create(section=section_10b, subject=sub_sci, defaults={"teacher": teachers[1]})
            ClassSubjectTeacher.objects.get_or_create(section=section_10b, subject=sub_eng, defaults={"teacher": teachers[2]})

            # 5. Student Enrollments
            StudentEnrollment.objects.get_or_create(
                student=students[0],
                academic_year=academic_year,
                defaults={"section": section_10a, "roll_number": "101"}
            )
            StudentEnrollment.objects.get_or_create(
                student=students[1],
                academic_year=academic_year,
                defaults={"section": section_10a, "roll_number": "102"}
            )
            StudentEnrollment.objects.get_or_create(
                student=students[2],
                academic_year=academic_year,
                defaults={"section": section_10b, "roll_number": "201"}
            )
            StudentEnrollment.objects.get_or_create(
                student=students[3],
                academic_year=academic_year,
                defaults={"section": section_10b, "roll_number": "202"}
            )

            # 6. Grading Scale & Rules
            scale, _ = GradingScale.objects.get_or_create(
                name="Standard 10-Point Scale",
                defaults={"description": "Standard letter grade scale with grade points"}
            )
            rules_config = [
                ("A+", Decimal("90.00"), Decimal("100.00"), Decimal("4.00"), "Outstanding"),
                ("A", Decimal("80.00"), Decimal("89.99"), Decimal("3.70"), "Excellent"),
                ("B", Decimal("70.00"), Decimal("79.99"), Decimal("3.00"), "Very Good"),
                ("C", Decimal("60.00"), Decimal("69.99"), Decimal("2.00"), "Satisfactory"),
                ("D", Decimal("40.00"), Decimal("59.99"), Decimal("1.00"), "Pass"),
                ("F", Decimal("0.00"), Decimal("39.99"), Decimal("0.00"), "Fail"),
            ]
            for g, min_p, max_p, gp, rem in rules_config:
                GradeRule.objects.get_or_create(
                    grading_scale=scale,
                    grade=g,
                    defaults={"min_percentage": min_p, "max_percentage": max_p, "grade_point": gp, "remarks": rem}
                )

            # 7. Exams & Marks
            exam, _ = Exam.objects.get_or_create(
                name="Mid-Term Assessment 2026",
                academic_year=academic_year,
                defaults={
                    "start_date": date(2026, 10, 10),
                    "end_date": date(2026, 10, 20),
                    "grading_scale": scale,
                    "is_published": True,
                }
            )

            es_math, _ = ExamSubject.objects.get_or_create(
                exam=exam, subject=sub_math, class_grade=grade10,
                defaults={"max_marks": Decimal("100.00"), "pass_marks": Decimal("40.00")}
            )
            es_sci, _ = ExamSubject.objects.get_or_create(
                exam=exam, subject=sub_sci, class_grade=grade10,
                defaults={"max_marks": Decimal("100.00"), "pass_marks": Decimal("40.00")}
            )
            es_eng, _ = ExamSubject.objects.get_or_create(
                exam=exam, subject=sub_eng, class_grade=grade10,
                defaults={"max_marks": Decimal("100.00"), "pass_marks": Decimal("40.00")}
            )

            sample_marks = [
                (es_math, students[0], Decimal("92.50")),  # Alice -> A+
                (es_sci, students[0], Decimal("88.00")),   # Alice -> A
                (es_eng, students[0], Decimal("94.00")),   # Alice -> A+
                (es_math, students[1], Decimal("74.00")),  # Leo -> B
                (es_sci, students[1], Decimal("68.50")),   # Leo -> C
                (es_eng, students[1], Decimal("81.00")),   # Leo -> A
                (es_math, students[2], Decimal("85.00")),  # Sofia -> A
                (es_sci, students[2], Decimal("91.00")),   # Sofia -> A+
                (es_eng, students[2], Decimal("89.00")),   # Sofia -> A
            ]
            for es, st, m in sample_marks:
                ExamResult.objects.get_or_create(
                    exam_subject=es,
                    student=st,
                    defaults={"marks_obtained": m}
                )

            # 8. Attendance Sessions (Past 3 days)
            today = date.today()
            for days_ago in range(3, -1, -1):
                session_date = today - timedelta(days=days_ago)
                for sec, teacher in [(section_10a, teachers[0]), (section_10b, teachers[1])]:
                    sess, _ = AttendanceSession.objects.get_or_create(
                        date=session_date,
                        section=sec,
                        defaults={
                            "academic_year": academic_year,
                            "taken_by": teacher,
                        }
                    )
                    # Add records for students enrolled in this section
                    enrollments = sec.student_enrollments.filter(is_active=True)
                    for idx, enr in enumerate(enrollments):
                        # Give Alice 100% attendance, Leo 1 excused absence
                        status_choice = AttendanceStatus.PRESENT
                        remarks_txt = "On time"
                        if enr.student == students[1] and days_ago == 1:
                            status_choice = AttendanceStatus.EXCUSED
                            remarks_txt = "Medical leave"

                        AttendanceRecord.objects.get_or_create(
                            session=sess,
                            student=enr.student,
                            defaults={"status": status_choice, "remarks": remarks_txt}
                        )

            # 9. Fee Structures & Invoices
            cat_tuition, _ = FeeCategory.objects.get_or_create(name="Term Tuition Fee")
            cat_lab, _ = FeeCategory.objects.get_or_create(name="Science & Computer Lab Fee")

            fs_tuition, _ = FeeStructure.objects.get_or_create(
                category=cat_tuition,
                class_grade=grade10,
                academic_year=academic_year,
                defaults={"amount": Decimal("1200.00"), "due_date": today + timedelta(days=30)}
            )
            fs_lab, _ = FeeStructure.objects.get_or_create(
                category=cat_lab,
                class_grade=grade10,
                academic_year=academic_year,
                defaults={"amount": Decimal("300.00"), "due_date": today + timedelta(days=30)}
            )

            # Invoices
            inv1, _ = FeeInvoice.objects.get_or_create(
                invoice_number="INV-2026-001",
                defaults={
                    "student": students[0],
                    "fee_structure": fs_tuition,
                    "total_amount": Decimal("1200.00"),
                    "due_date": today + timedelta(days=30),
                }
            )
            inv2, _ = FeeInvoice.objects.get_or_create(
                invoice_number="INV-2026-002",
                defaults={
                    "student": students[1],
                    "fee_structure": fs_tuition,
                    "total_amount": Decimal("1200.00"),
                    "due_date": today + timedelta(days=30),
                }
            )
            inv3, _ = FeeInvoice.objects.get_or_create(
                invoice_number="INV-2026-003",
                defaults={
                    "student": students[2],
                    "fee_structure": fs_lab,
                    "total_amount": Decimal("300.00"),
                    "due_date": today + timedelta(days=30),
                }
            )

            # Payments
            # Alice pays in full
            p1, _ = FeePayment.objects.get_or_create(
                transaction_reference="SIM-TXN-001",
                defaults={
                    "invoice": inv1,
                    "amount": Decimal("1200.00"),
                    "payment_method": PaymentMethod.SIMULATED_CARD,
                    "recorded_by": admin_user,
                    "notes": "Full annual payment via portal",
                }
            )
            inv1.reconcile_ledger()

            # Leo makes partial payment of $700
            p2, _ = FeePayment.objects.get_or_create(
                transaction_reference="SIM-TXN-002",
                defaults={
                    "invoice": inv2,
                    "amount": Decimal("700.00"),
                    "payment_method": PaymentMethod.SIMULATED_BANK,
                    "recorded_by": admin_user,
                    "notes": "First installment paid",
                }
            )
            inv2.reconcile_ledger()

            # inv3 is unpaid for Sofia

            # 10. Audit Logs
            log_action(admin_user, 'CREATE', 'AcademicYear', academic_year.id, str(academic_year), "Initialized academic calendar.")
            log_action(admin_user, 'PAYMENT', 'FeePayment', p1.id, p1.transaction_reference, "Settled full tuition fee for Alice Taylor.")
            log_action(teachers[0].user, 'ATTENDANCE', 'AttendanceSession', 1, "Grade 10 - Section A", "Logged daily classroom headcount.")

        self.stdout.write(self.style.SUCCESS("Database successfully seeded with realistic school operations!"))
        self.stdout.write(self.style.SUCCESS("""
Demo Accounts Created:
-----------------------------------------------------------
Admin:    username: admin      | password: admin123
Teacher:  username: teacher1   | password: teacher123
Guardian: username: guardian1  | password: guardian123
Student:  username: student1   | password: student123
-----------------------------------------------------------
        """))

