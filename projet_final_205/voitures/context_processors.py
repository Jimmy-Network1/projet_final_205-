from __future__ import annotations

from voitures.models import Notification


def notification_counts(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"unread_notifications_count": 0}
    return {
        "unread_notifications_count": Notification.objects.filter(
            utilisateur=request.user, lu=False
        ).count()
    }

