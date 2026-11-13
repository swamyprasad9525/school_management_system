from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin
from .models import Role

def role_required(allowed_roles):
    """
    Decorator for views that checks that the user is logged in and has an allowed role.
    Raises PermissionDenied (HTTP 403) if role doesn't match.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this resource.")
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required([Role.ADMIN])(view_func)

def teacher_required(view_func):
    return role_required([Role.TEACHER])(view_func)

def guardian_required(view_func):
    return role_required([Role.GUARDIAN])(view_func)

def student_required(view_func):
    return role_required([Role.STUDENT])(view_func)

def guardian_or_student_required(view_func):
    return role_required([Role.GUARDIAN, Role.STUDENT])(view_func)


class RoleRequiredMixin(AccessMixin):
    """
    CBV Mixin to enforce role-based access.
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied("You do not have permission to access this resource.")
        return super().dispatch(request, *args, **kwargs)

