import uuid
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from accounts.permissions import role_required, Role
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

    return render(request, 'finance/invoices_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': InvoiceStatus.choices,
    })

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
    # Privacy check: Guardian can ONLY pay their own child's invoice
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
                # Generate unique transaction reference
                txn_ref = f"SIM-{uuid.uuid4().hex[:10].upper()}"

                # Create Payment
                payment = FeePayment.objects.create(
                    invoice=invoice,
                    transaction_reference=txn_ref,
                    amount=payment_amount,
                    payment_method=method_val,
                    recorded_by=user,
                    notes=notes_val
                )

                # Reconcile invoice ledger
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
    """
    Renders an official, printable payment receipt with transaction verification.
    """
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
    """
    Comprehensive fee ledger reconciliation report.
    Reconciles: Total Invoiced = Total Collected + Outstanding Balance.
    """
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
