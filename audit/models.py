from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Created Record'),
        ('UPDATE', 'Updated Record'),
        ('DELETE', 'Deleted Record'),
        ('ATTENDANCE', 'Recorded Attendance'),
        ('MARKS_ENTRY', 'Entered / Updated Marks'),
        ('PAYMENT', 'Recorded Fee Payment'),
        ('INVOICE_GEN', 'Generated Fee Invoice'),
        ('SECURITY', 'Security / Auth Event'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name']),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'System'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor_name} -> {self.get_action_display()} on {self.model_name} ({self.object_repr})"

def log_action(actor=None, action='UPDATE', model_name='', object_id='', object_repr='', details='', ip_address=None):
    """
    Utility function to record audit events safely.
    """
    try:
        AuditLog.objects.create(
            actor=actor,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            object_repr=str(object_repr)[:255],
            details=str(details),
            ip_address=ip_address,
        )
    except Exception as e:
        # Prevent audit logging failure from breaking primary business flow
        print(f"Failed to record audit log: {e}")
