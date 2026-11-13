from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError

class FeeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Fee Categories'

    def __str__(self):
        return self.name


class FeeStructure(models.Model):
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name='structures')
    class_grade = models.ForeignKey('academics.ClassGrade', on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE, related_name='fee_structures')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['category', 'class_grade', 'academic_year'], name='unique_category_grade_year_fee')
        ]

    def __str__(self):
        return f"{self.category.name} - {self.class_grade.name}: ${self.amount} ({self.academic_year.name})"


class InvoiceStatus(models.TextChoices):
    UNPAID = 'UNPAID', 'Unpaid'
    PARTIAL = 'PARTIAL', 'Partially Paid'
    PAID = 'PAID', 'Paid in Full'


class FeeInvoice(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='fee_invoices')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='invoices')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=15, choices=InvoiceStatus.choices, default=InvoiceStatus.UNPAID)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()

    class Meta:
        ordering = ['-issue_date']

    @property
    def balance(self):
        return max(Decimal('0.00'), self.total_amount - self.paid_amount)

    def reconcile_ledger(self):
        """
        Recalculates paid_amount directly from the sum of associated payments.
        Maintains absolute invariant:
        paid_amount = Sum(payments.amount)
        status matches paid_amount vs total_amount.
        """
        total_paid = self.payments.aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0.00')
        self.paid_amount = total_paid
        if self.paid_amount >= self.total_amount:
            self.status = InvoiceStatus.PAID
        elif self.paid_amount > Decimal('0.00'):
            self.status = InvoiceStatus.PARTIAL
        else:
            self.status = InvoiceStatus.UNPAID
        self.save()

    def __str__(self):
        return f"{self.invoice_number} | {self.student} - Due: ${self.balance}"


class PaymentMethod(models.TextChoices):
    SIMULATED_CARD = 'SIMULATED_CARD', 'Simulated Card Payment'
    SIMULATED_BANK = 'SIMULATED_BANK', 'Simulated Bank Transfer'
    SIMULATED_CASH = 'SIMULATED_CASH', 'Simulated Cash Payment'


class FeePayment(models.Model):
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name='payments')
    transaction_reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices, default=PaymentMethod.SIMULATED_CARD)
    payment_date = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-payment_date']

    def clean(self):
        if self.amount <= Decimal('0.00'):
            raise ValidationError("Payment amount must be greater than zero.")
        if self.amount > self.invoice.balance:
            raise ValidationError(f"Payment amount (${self.amount}) exceeds invoice remaining balance (${self.invoice.balance}).")

    def __str__(self):
        return f"Payment {self.transaction_reference} - ${self.amount} on {self.invoice.invoice_number}"
