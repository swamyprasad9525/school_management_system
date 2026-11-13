from django.shortcuts import render
from django.core.paginator import Paginator
from accounts.permissions import admin_required
from .models import AuditLog

@admin_required
def logs_list(request):
    action_filter = request.GET.get('action', '')
    search_query = request.GET.get('q', '')

    logs = AuditLog.objects.select_related('actor').all()
    if action_filter:
        logs = logs.filter(action=action_filter)
    if search_query:
        logs = logs.filter(object_repr__icontains=search_query) | logs.filter(details__icontains=search_query)

    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'search_query': search_query,
        'action_choices': AuditLog.ACTION_CHOICES,
    }
    return render(request, 'audit/logs_list.html', context)
