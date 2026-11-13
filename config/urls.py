"""
URL configuration for the School Management System.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.api import StudentViewSet, AttendanceSessionViewSet, ExamResultViewSet, FeeInvoiceViewSet

# API Router
router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='api-students')
router.register(r'attendance', AttendanceSessionViewSet, basename='api-attendance')
router.register(r'exam-results', ExamResultViewSet, basename='api-exam-results')
router.register(r'invoices', FeeInvoiceViewSet, basename='api-invoices')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # SMS Web Modules
    path('accounts/', include('accounts.urls')),
    path('academics/', include('academics.urls')),
    path('attendance/', include('attendance.urls')),
    path('examinations/', include('examinations.urls')),
    path('finance/', include('finance.urls')),
    path('audit/', include('audit.urls')),
    path('', include('core.urls')),

    # REST APIs
    path('api/v1/', include(router.urls)),

    # OpenAPI 3.0 / Swagger Interactive Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Development Media & Static Handling
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
