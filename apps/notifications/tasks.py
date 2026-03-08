from celery import shared_task
from django.core.mail import send_mail


@shared_task
def notify_pending_registration(user_id, estate_id):
    """Tells estate managers a new registration is waiting for approval."""
    from apps.authentication.models import User, EstateMembership
    from apps.estates.models import Estate

    user   = User.objects.get(id=user_id)
    estate = Estate.objects.get(id=estate_id)

    # Get all managers for this estate
    managers = EstateMembership.objects.filter(
        estate=estate,
        role__in=["estate_admin", "estate_manager"],
        is_active=True,
    ).select_related("user")

    for m in managers:
        if m.user.email:
            send_mail(
                subject=f"[{estate.name}] New registration pending approval",
                message=(
                    f"Hi {m.user.first_name},\n\n"
                    f"{user.get_full_name()} ({user.email}) has registered "
                    f"and is waiting for your approval.\n\n"
                    f"Log in to review: http://yoursite.com/admin/pending"
                ),
                from_email="noreply@residentialos.com",
                recipient_list=[m.user.email],
            )


@shared_task
def notify_new_member(user_id, estate_id, auto_approved=False):
    """Tells managers a new member joined via invite link."""
    from apps.authentication.models import User, EstateMembership
    from apps.estates.models import Estate

    user   = User.objects.get(id=user_id)
    estate = Estate.objects.get(id=estate_id)

    managers = EstateMembership.objects.filter(
        estate=estate,
        role__in=["estate_admin", "estate_manager"],
        is_active=True,
    ).select_related("user")

    for m in managers:
        if m.user.email:
            send_mail(
                subject=f"[{estate.name}] New member joined via invite",
                message=(
                    f"Hi {m.user.first_name},\n\n"
                    f"{user.get_full_name()} ({user.email}) has joined "
                    f"{estate.name} via an invite link and is now active."
                ),
                from_email="noreply@residentialos.com",
                recipient_list=[m.user.email],
            )


@shared_task
def notify_registration_approved(user_id, estate_id):
    """Tells the resident their account has been approved."""
    from apps.authentication.models import User
    from apps.estates.models import Estate

    user   = User.objects.get(id=user_id)
    estate = Estate.objects.get(id=estate_id)

    if user.email:
        send_mail(
            subject=f"[{estate.name}] Your registration has been approved!",
            message=(
                f"Hi {user.first_name},\n\n"
                f"Great news! Your registration for {estate.name} "
                f"has been approved. You can now log in.\n\n"
                f"Log in here: http://yoursite.com/login"
            ),
            from_email="noreply@residentialos.com",
            recipient_list=[user.email],
        )


@shared_task
def notify_registration_rejected(user_id, estate_id, reason=""):
    from apps.authentication.models import User
    from apps.estates.models import Estate

    user   = User.objects.get(id=user_id)
    estate = Estate.objects.get(id=estate_id)

    if user.email:
        reason_block = f"\n\nReason:\n{reason}\n" if reason else ""
        send_mail(
            subject=f"[{estate.name}] Your registration was not approved",
            message=(
                f"Dear {user.first_name},\n\n"
                f"Unfortunately your registration for {estate.name} "
                f"was not approved at this time."
                f"{reason_block}\n"
                f"If you believe this is an error or would like more information, "
                f"please contact the estate office directly.\n\n"
                f"Regards,\n{estate.name}"
            ),
            from_email="noreply@residentialos.com",
            recipient_list=[user.email],
        )


@shared_task
def dispatch_announcement(announcement_id):
    from apps.announcements.models import Announcement
    from apps.residents.models import Resident

    announcement = Announcement.objects.select_related("estate").get(id=announcement_id)
    if not announcement.send_email:
        return

    recipients = Resident.objects.filter(
        estate=announcement.estate, is_active=True
    ).exclude(email="").values_list("email", flat=True)

    for email in recipients:
        send_mail(
            subject=f"[{announcement.estate.name}] {announcement.title}",
            message=announcement.body,
            from_email="noreply@residentialos.com",
            recipient_list=[email],
        )