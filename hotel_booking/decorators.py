from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if request.user.role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and (u.role == 'admin' or u.is_superuser))(view_func)

def manager_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and (u.role == 'manager' or u.role == 'admin'))(view_func)