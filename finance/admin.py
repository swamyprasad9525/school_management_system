from django.contrib import admin
from .models import FeeCategory, FeeStructure, FeeInvoice, FeePayment

class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    readonly_fields = ('transaction_reference', 'payment_date')

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('category', 'class_grade', 'academic_year', 'amount', 'due_date')
    list_filter = ('class_grade', 'academic_year')

@admin.register(FeeInvoice)
class FeeInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'fee_structure', 'total_amount', 'paid_amount', 'status', 'due_date')
    list_filter = ('status', 'due_date')
    search_fields = ('invoice_number', 'student__admission_number', 'student__user__first_name', 'student__user__last_name')
    inlines = [FeePaymentInline]

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_reference', 'invoice', 'amount', 'payment_method', 'payment_date')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('transaction_reference', 'invoice__invoice_number')
