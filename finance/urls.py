from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('invoices/', views.invoices_list, name='invoices_list'),
    path('structures/', views.fee_structures, name='fee_structures'),
    path('pay/<int:invoice_id>/', views.record_payment, name='record_payment'),
    path('receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
    path('ledger/', views.ledger_report, name='ledger_report'),
]
