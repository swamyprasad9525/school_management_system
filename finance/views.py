import uuid
from decimal import Decimal
from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from accounts.permissions import role_required, admin_required, Role
from accounts.models import StudentProfile
from audit.models import log_action
from .models import FeeCategory, FeeStructure, FeeInvoice, FeePayment, InvoiceStatus, PaymentMethod

@role_required([Role.ADMIN, Role.GUARDIAN, Role.STUDENT])
def invoices_list(request):
    """
    Lists student fee invoices.
    Guardians can ONLY view their linked children's invoices.
    """
    user = request.user
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')

    queryset = FeeInvoice.objects.select_related(
        'student__user', 'student__guardian__user', 'fee_structure__category', 'fee_structure__class_grade'
    ).all()

    if user.is_guardian_role:
        queryset = queryset.filter(student__guardian=user.guardian_profile)
    elif user.is_student_role:
        queryset = queryset.filter(student=user.student_profile)

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if search_query:
        queryset = queryset.filter(
            invoice_number__icontains=search_query
        ) | queryset.filter(
            student__user__first_name__icontains=search_query
        ) | queryset.filter(
            student__user__last_name__icontains=search_query
        )

    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_students = StudentProfile.objects.select_related('user').all() if user.is_admin_role else []
    all_structures = FeeStructure.objects.select_related('category', 'class_grade').all() if user.is_admin_role else []

    return render(request, 'finance/invoices_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': InvoiceStatus.choices,
        'all_students': all_students,
        'all_structures': all_structures,
    })

@admin_required
def generate_invoice(request):
    """
    Modal endpoint to generate a new fee invoice for a student.
    """
    if request.method == 'POST':
        student_id = request.POST.get('student')
        structure_id = request.POST.get('fee_structure')
        due_date_str = request.POST.get('due_date')

        if not (student_id and structure_id):
            messages.error(request, "Please select both a student and a fee structure.")
            return redirect('finance:invoices_list')

        student = get_object_or_404(StudentProfile, id=student_id)
        structure = get_object_or_404(FeeStructure, id=structure_id)
        due_date_val = date.fromisoformat(due_date_str) if due_date_str else (date.today() + timedelta(days=30))

        inv_num = f"INV-2026-{uuid.uuid4().hex[:5].upper()}"

        with transaction.atomic():
            invoice = FeeInvoice.objects.create(
                invoice_number=inv_num,
                student=student,
                fee_structure=structure,
                total_amount=structure.amount,
                due_date=due_date_val
            )

            log_action(
                actor=request.user,
                action='CREATE',
                model_name='FeeInvoice',
                object_id=invoice.id,
                object_repr=f"{inv_num} (${structure.amount})",
                details=f"Generated invoice for {student}. Category: {structure.category.name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

        messages.success(request, f"Invoice {inv_num} for ${structure.amount} issued to {student}!")
    return redirect('finance:invoices_list')

@role_required([Role.ADMIN])
def fee_structures(request):
    structures = FeeStructure.objects.select_related('category', 'class_grade', 'academic_year').all()
    categories = FeeCategory.objects.all()
    return render(request, 'finance/fee_structures.html', {
        'structures': structures,
        'categories': categories,
    })

@role_required([Role.ADMIN, Role.GUARDIAN])
def record_payment(request, invoice_id):
    """
    Processes simulated fee payments.
    Guarantees transactional integrity & ledger reconciliation.
    """
    invoice = get_object_or_404(
        FeeInvoice.objects.select_related('student__user', 'student__guardian__user', 'fee_structure__category'),
        id=invoice_id
    )

    user = request.user
    if user.is_guardian_role and invoice.student.guardian != user.guardian_profile:
        raise PermissionDenied("Access Denied: You cannot make payments for this invoice.")

    if request.method == 'POST':
        amount_str = request.POST.get('amount', '').strip()
        method_val = request.POST.get('payment_method', PaymentMethod.SIMULATED_CARD)
        notes_val = request.POST.get('notes', 'Simulated online portal payment')

        try:
            payment_amount = Decimal(amount_str)
            if payment_amount <= Decimal('0.00'):
                messages.error(request, "Payment amount must be greater than zero.")
                return redirect('finance:record_payment', invoice_id=invoice.id)
            if payment_amount > invoice.balance:
                messages.error(request, f"Payment amount (${payment_amount}) exceeds outstanding balance (${invoice.balance}).")
                return redirect('finance:record_payment', invoice_id=invoice.id)

            with transaction.atomic():
                txn_ref = f"SIM-{uuid.uuid4().hex[:10].upper()}"

                payment = FeePayment.objects.create(
                    invoice=invoice,
                    transaction_reference=txn_ref,
                    amount=payment_amount,
                    payment_method=method_val,
                    recorded_by=user,
                    notes=notes_val
                )

                invoice.reconcile_ledger()

                log_action(
                    actor=user,
                    action='PAYMENT',
                    model_name='FeePayment',
                    object_id=payment.id,
                    object_repr=f"{txn_ref} (${payment_amount})",
                    details=f"Payment for invoice {invoice.invoice_number}. New balance: ${invoice.balance}.",
                    ip_address=request.META.get('REMOTE_ADDR')
                )

                messages.success(request, f"Payment of ${payment_amount} successfully recorded! Transaction Reference: {txn_ref}.")
                return redirect('finance:payment_receipt', payment_id=payment.id)

        except (ValueError, TypeError, ValidationError) as e:
            messages.error(request, f"Invalid payment request: {e}")

    return render(request, 'finance/record_payment.html', {
        'invoice': invoice,
        'payment_methods': PaymentMethod.choices,
    })

@role_required([Role.ADMIN, Role.GUARDIAN, Role.STUDENT])
def payment_receipt(request, payment_id):
    payment = get_object_or_404(
        FeePayment.objects.select_related('invoice__student__user', 'invoice__student__guardian__user', 'invoice__fee_structure__category', 'recorded_by'),
        id=payment_id
    )
    user = request.user
    student = payment.invoice.student

    if user.is_guardian_role and student.guardian != user.guardian_profile:
        raise PermissionDenied("Access Denied: You cannot view receipts for other students.")
    elif user.is_student_role and student != user.student_profile:
        raise PermissionDenied("Access Denied: You cannot view other students' receipts.")

    return render(request, 'finance/payment_receipt.html', {
        'payment': payment,
        'invoice': payment.invoice,
        'student': student,
    })

@role_required([Role.ADMIN])
def ledger_report(request):
    invoices = FeeInvoice.objects.all()
    total_invoiced = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_collected = invoices.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0.00')
    outstanding_balance = total_invoiced - total_collected

    recent_payments = FeePayment.objects.select_related('invoice__student__user', 'recorded_by').all()[:20]

    return render(request, 'finance/ledger_report.html', {
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'outstanding_balance': outstanding_balance,
        'recent_payments': recent_payments,
        'total_invoices_count': invoices.count(),
        'paid_invoices_count': invoices.filter(status=InvoiceStatus.PAID).count(),
        'partial_invoices_count': invoices.filter(status=InvoiceStatus.PARTIAL).count(),
        'unpaid_invoices_count': invoices.filter(status=InvoiceStatus.UNPAID).count(),
    })
