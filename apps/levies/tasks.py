from celery import shared_task
from datetime import date


def get_levy_rate_for_unit(estate, unit, billing_month):
    """
    Finds the best matching active LevyRate for a unit on a given date.

    Priority order (most specific wins):
      1. Matches unit_type + bedrooms + size range
      2. Matches unit_type + bedrooms
      3. Matches unit_type + size range
      4. Matches unit_type only
      5. Estate default (no type/bedroom/size filters)

    Falls back to estate.monthly_levy_amount if no rate found.
    """
    from apps.levies.models import LevyRate

    # Get all active rates for this estate valid on billing_month
    rates = LevyRate.objects.filter(
        estate=estate,
        is_active=True,
        effective_from__lte=billing_month,
    ).filter(
        models.Q(effective_to__isnull=True) |
        models.Q(effective_to__gte=billing_month)
    )

    matching = [rate for rate in rates if rate.matches_unit(unit)]

    if not matching:
        return None, estate.monthly_levy_amount

    # Score each match — more specific = higher score
    def specificity_score(rate):
        score = 0
        if rate.unit_type:
            score += 10
        if rate.bedrooms is not None:
            score += 5
        if rate.min_size_sqm is not None or rate.max_size_sqm is not None:
            score += 3
        return score

    best_rate = max(matching, key=specificity_score)
    return best_rate, best_rate.amount


@shared_task
def generate_monthly_levies():
    """
    Runs on the 1st of each month at 00:05.
    Creates LevyBilling for all occupied units, using the most
    specific matching LevyRate for each unit.
    """
    from django.db import models
    from apps.estates.models import Estate
    from apps.residents.models import Unit
    from apps.levies.models import LevyBilling

    today         = date.today()
    billing_month = today.replace(day=1)

    for estate in Estate.objects.filter(is_active=True):
        for unit in Unit.objects.filter(estate=estate, is_occupied=True):
            resident   = unit.residents.filter(is_active=True).first()
            rate, amount = get_levy_rate_for_unit(estate, unit, billing_month)

            if not amount:
                continue  # No rate configured, skip this unit

            LevyBilling.objects.get_or_create(
                estate=estate,
                unit=unit,
                billing_month=billing_month,
                defaults={
                    "amount_due": amount,
                    "due_date":   billing_month.replace(day=estate.levy_due_day),
                    "resident":   resident,
                    "levy_rate":  rate,
                },
            )


@shared_task
def send_overdue_reminders():
    from apps.levies.models import LevyBilling
    from django.core.mail import send_mail

    overdue = LevyBilling.objects.filter(
        status="overdue"
    ).select_related("resident", "unit", "levy_rate")

    for billing in overdue:
        if billing.resident and billing.resident.email:
            send_mail(
                subject=f"Levy Reminder — {billing.billing_month:%B %Y}",
                message=(
                    f"Dear {billing.resident.full_name},\n\n"
                    f"Your levy of R{billing.amount_due} for "
                    f"{billing.billing_month:%B %Y} is overdue.\n"
                    f"Outstanding balance: R{billing.balance}\n\n"
                    f"Please arrange payment at your earliest convenience."
                ),
                from_email="noreply@residentialos.com",
                recipient_list=[billing.resident.email],
            )