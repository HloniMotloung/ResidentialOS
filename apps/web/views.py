from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.authentication.models import EstateMembership, EstateInvite
from apps.authentication.serializers import SelfRegisterSerializer
from apps.estates.models import Estate


# ── HELPERS ──────────────────────────────────────────────────────────────────

def get_estate_and_role(request):
    """Returns (estate, role) for the current user's session."""
    slug = request.session.get('estate_slug')
    if not slug:
        return None, None
    try:
        estate = Estate.objects.get(slug=slug)
        membership = EstateMembership.objects.get(
            user=request.user, estate=estate, is_active=True
        )
        return estate, membership.role
    except (Estate.DoesNotExist, EstateMembership.DoesNotExist):
        return None, None


def pending_count(request):
    """Helper to get pending registration count for sidebar badge."""
    if not request.user.is_authenticated:
        return 0
    estate, role = get_estate_and_role(request)
    if estate and role in ['superadmin', 'estate_admin', 'estate_manager']:
        return EstateMembership.objects.filter(estate=estate, status='pending').count()
    return 0


# ── AUTH VIEWS ────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('web:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'web/auth/login.html')

        if user.status == 'pending':
            messages.warning(request, 'Your account is pending approval by the estate manager.')
            return render(request, 'web/auth/login.html')

        if user.status == 'rejected':
            messages.error(request, 'Your registration was not approved. Please contact the estate manager.')
            return render(request, 'web/auth/login.html')

        login(request, user)

        # Set session vars — pick first active membership
        membership = EstateMembership.objects.filter(
            user=user, is_active=True
        ).select_related('estate').first()

        if membership:
            request.session['estate_slug'] = membership.estate.slug
            request.session['estate_name'] = membership.estate.name
            request.session['estate_id'] = str(membership.estate.id)
            request.session['user_role']   = membership.role
        elif user.is_superuser:
            request.session['user_role'] = 'superadmin'

        return redirect('web:dashboard')

    return render(request, 'web/auth/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('web:dashboard')

    if request.method == 'POST':
        data = request.POST.dict()
        # Normalise invite code to uppercase
        if data.get('invite_code'):
            data['invite_code'] = data['invite_code'].strip().upper()

        serializer = SelfRegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            if user.status == 'approved':
                login(request, user)
                membership = EstateMembership.objects.filter(
                    user=user, is_active=True
                ).select_related('estate').first()
                if membership:
                    request.session['estate_slug'] = membership.estate.slug
                    request.session['estate_name'] = membership.estate.name
                    request.session['estate_id'] = str(membership.estate.id)
                    request.session['user_role']   = membership.role
                messages.success(request, f'Welcome to ResidentialOS, {user.first_name}!')
                return redirect('web:dashboard')
            else:
                messages.success(
                    request,
                    'Registration submitted! You will receive an email once approved by the estate manager.'
                )
                return redirect('web:login')
        else:
            for field, errors in serializer.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')

    from apps.estates.models import Estate
    estates = Estate.objects.filter(is_active=True).order_by('name')
    return render(request, 'web/auth/register.html', {'estates': estates})


@require_POST
@login_required
def logout_view(request):
    logout(request)
    return redirect('web:login')


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    estate, role = get_estate_and_role(request)
    if not estate:
        messages.warning(request, 'You are not assigned to an estate yet.')
        return render(request, 'web/dashboard/index.html', {'stats': {}, 'pending_count': 0})

    from apps.residents.models import Unit, Resident
    from apps.levies.models import LevyBilling
    from apps.maintenance.models import MaintenanceRequest
    from apps.visitors.models import GateLog

    today       = timezone.now().date()
    month_start = today.replace(day=1)

    units     = Unit.objects.filter(estate=estate)
    residents = Resident.objects.filter(estate=estate, is_active=True)
    billings  = LevyBilling.objects.filter(estate=estate)
    maint     = MaintenanceRequest.objects.filter(estate=estate)
    gate      = GateLog.objects.filter(estate=estate)

    stats = {
        'units':     {'total': units.count(), 'occupied': units.filter(is_occupied=True).count(), 'vacant': units.filter(is_occupied=False).count()},
        'residents': {'total': residents.count(), 'owners': residents.filter(resident_type='owner').count(), 'tenants': residents.filter(resident_type='tenant').count()},
        'levies': {
            'outstanding_count':    billings.filter(status='outstanding').count(),
            'overdue_count':        billings.filter(status='overdue').count(),
            'outstanding_amount':   billings.filter(status__in=['outstanding', 'overdue', 'partial']).aggregate(t=Sum('amount_due'))['t'] or 0,
            'collected_this_month': billings.filter(billing_month=month_start, status='paid').aggregate(t=Sum('amount_due'))['t'] or 0,
        },
        'maintenance': {'open': maint.filter(status='open').count(), 'in_progress': maint.filter(status='in_progress').count(), 'critical': maint.filter(priority='critical', status__in=['open', 'in_progress']).count()},
        'visitors':   {'inside_now': gate.filter(exit_time__isnull=True).count(), 'today_total': gate.filter(entry_time__date=today).count(), 'month_total': gate.filter(entry_time__date__gte=month_start).count()},
    }

    recent_maintenance  = maint.filter(status__in=['open', 'in_progress']).order_by('-created_at')[:5]
    overdue_levies      = billings.filter(status='overdue').select_related('unit', 'resident').order_by('-billing_month')[:5]
    pending_regs        = EstateMembership.objects.filter(estate=estate, status='pending').select_related('user')[:5]

    return render(request, 'web/dashboard/index.html', {
        'stats':                stats,
        'recent_maintenance':   recent_maintenance,
        'overdue_levies':       overdue_levies,
        'pending_registrations': pending_regs,
        'pending_count':        pending_regs.count(),
    })


# ── RESIDENTS ─────────────────────────────────────────────────────────────────

@login_required
def residents_list(request):
    from apps.residents.models import Resident
    estate, role = get_estate_and_role(request)
    residents = Resident.objects.filter(estate=estate).select_related('unit').order_by('last_name', 'first_name') if estate else []
    return render(request, 'web/residents/list.html', {'residents': residents, 'pending_count': pending_count(request)})


@login_required
def resident_detail(request, pk):
    from apps.residents.models import Resident
    from apps.levies.models import LevyBilling
    estate, role = get_estate_and_role(request)
    resident = get_object_or_404(Resident, pk=pk, estate=estate)
    billings = LevyBilling.objects.filter(resident=resident).order_by('-billing_month')[:12]
    return render(request, 'web/residents/detail.html', {'resident': resident, 'billings': billings, 'pending_count': pending_count(request)})


@login_required
def resident_add(request):
    from apps.residents.models import Unit
    estate, role = get_estate_and_role(request)
    if role not in ['superadmin', 'estate_admin', 'estate_manager']:
        messages.error(request, 'You do not have permission to add residents.')
        return redirect('web:residents')

    if request.method == 'POST':
        from apps.residents.models import Resident
        unit_id = request.POST.get('unit')
        unit = Unit.objects.filter(id=unit_id, estate=estate).first() if unit_id else None
        Resident.objects.create(
            estate=estate,
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            resident_type=request.POST.get('resident_type', 'tenant'),
            unit=unit,
            move_in_date=request.POST.get('move_in_date') or None,
        )
        if unit:
            unit.is_occupied = True
            unit.save(update_fields=['is_occupied'])
        messages.success(request, 'Resident added successfully.')
        return redirect('web:residents')

    units = Unit.objects.filter(estate=estate).order_by('unit_number')
    return render(request, 'web/residents/form.html', {'units': units, 'pending_count': pending_count(request)})


@login_required
def resident_edit(request, pk):
    from apps.residents.models import Resident, Unit
    estate, role = get_estate_and_role(request)
    resident = get_object_or_404(Resident, pk=pk, estate=estate)

    if request.method == 'POST':
        resident.first_name    = request.POST.get('first_name', resident.first_name)
        resident.last_name     = request.POST.get('last_name', resident.last_name)
        resident.email         = request.POST.get('email', resident.email)
        resident.phone         = request.POST.get('phone', resident.phone)
        resident.resident_type = request.POST.get('resident_type', resident.resident_type)
        unit_id = request.POST.get('unit')
        resident.unit = Unit.objects.filter(id=unit_id, estate=estate).first() if unit_id else None
        resident.save()
        messages.success(request, 'Resident updated.')
        return redirect('web:resident_detail', pk=resident.id)

    units = Unit.objects.filter(estate=estate).order_by('unit_number')
    return render(request, 'web/residents/form.html', {'resident': resident, 'units': units, 'pending_count': pending_count(request)})


# ── UNITS ─────────────────────────────────────────────────────────────────────

@login_required
def units_list(request):
    from apps.residents.models import Unit
    estate, role = get_estate_and_role(request)
    units = Unit.objects.filter(estate=estate).order_by('unit_number') if estate else []
    return render(request, 'web/residents/units.html', {'units': units, 'pending_count': pending_count(request)})


@login_required
def unit_add(request):
    from apps.residents.models import Unit
    estate, role = get_estate_and_role(request)
    if request.method == 'POST':
        Unit.objects.create(
            estate=estate,
            unit_number=request.POST['unit_number'],
            unit_type=request.POST.get('unit_type', 'apartment'),
            bedrooms=request.POST.get('bedrooms') or 0,
            bathrooms=request.POST.get('bathrooms') or 0,
            floor_size_sqm=request.POST.get('floor_size_sqm') or None,
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Unit added.')
        return redirect('web:units')
    return render(request, 'web/residents/unit_form.html', {'pending_count': pending_count(request)})


# ── LEVIES ────────────────────────────────────────────────────────────────────

@login_required
def levies_list(request):
    from apps.levies.models import LevyBilling
    estate, role = get_estate_and_role(request)
    qs = LevyBilling.objects.filter(estate=estate).select_related('unit', 'resident') if estate else LevyBilling.objects.none()

    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    billing_months = LevyBilling.objects.filter(estate=estate).dates('billing_month', 'month', order='DESC') if estate else []

    summary = {
        'total':       qs.count(),
        'overdue':     LevyBilling.objects.filter(estate=estate, status='overdue').count() if estate else 0,
        'outstanding': LevyBilling.objects.filter(estate=estate, status='outstanding').count() if estate else 0,
        'paid':        LevyBilling.objects.filter(estate=estate, status='paid').count() if estate else 0,
    }
    return render(request, 'web/levies/list.html', {'billings': qs, 'summary': summary, 'billing_months': billing_months, 'pending_count': pending_count(request)})


@login_required
def levy_detail(request, pk):
    from apps.levies.models import LevyBilling
    estate, role = get_estate_and_role(request)
    billing = get_object_or_404(LevyBilling, pk=pk, estate=estate)
    return render(request, 'web/levies/detail.html', {'billing': billing, 'pending_count': pending_count(request)})


@login_required
def levy_add(request):
    from apps.levies.models import LevyBilling
    from apps.residents.models import Unit, Resident
    estate, role = get_estate_and_role(request)
    if request.method == 'POST':
        unit = get_object_or_404(Unit, id=request.POST['unit'], estate=estate)
        resident_id = request.POST.get('resident')
        resident = Resident.objects.filter(id=resident_id).first() if resident_id else None
        from datetime import datetime
        billing_month_str = request.POST['billing_month']
        billing_month = datetime.strptime(billing_month_str, '%Y-%m').date().replace(day=1)
        LevyBilling.objects.create(
            estate=estate, unit=unit, resident=resident,
            billing_month=billing_month,
            amount_due=request.POST['amount_due'],
            due_date=request.POST['due_date'],
        )
        messages.success(request, 'Levy billing created.')
        return redirect('web:levies')
    units     = Unit.objects.filter(estate=estate)
    residents = Resident.objects.filter(estate=estate, is_active=True)
    return render(request, 'web/levies/form.html', {'units': units, 'residents': residents, 'pending_count': pending_count(request)})


@login_required
def levy_payment(request, pk):
    from apps.levies.models import LevyBilling, Payment
    estate, role = get_estate_and_role(request)
    billing = get_object_or_404(LevyBilling, pk=pk, estate=estate)
    if request.method == 'POST':
        Payment.objects.create(
            estate=estate,
            levy_billing=billing,
            resident=billing.resident,
            amount=request.POST['amount'],
            payment_date=request.POST['payment_date'],
            payment_method=request.POST.get('payment_method', 'eft'),
            reference=request.POST.get('reference', ''),
            recorded_by=request.user,
        )
        messages.success(request, 'Payment recorded successfully.')
        return redirect('web:levy_detail', pk=billing.id)
    return render(request, 'web/levies/payment_form.html', {'billing': billing, 'pending_count': pending_count(request)})


@login_required
def levy_rates(request):
    from apps.levies.models import LevyRate
    estate, role = get_estate_and_role(request)
    rates = LevyRate.objects.filter(estate=estate).order_by('unit_type', 'min_size_sqm') if estate else []
    return render(request, 'web/levies/rates.html', {'rates': rates, 'pending_count': pending_count(request)})


@login_required
def levy_rate_add(request):
    from apps.levies.models import LevyRate
    estate, role = get_estate_and_role(request)
    if request.method == 'POST':
        LevyRate.objects.create(
            estate=estate,
            name=request.POST['name'],
            unit_type=request.POST.get('unit_type', ''),
            bedrooms=request.POST.get('bedrooms') or None,
            min_size_sqm=request.POST.get('min_size_sqm') or None,
            max_size_sqm=request.POST.get('max_size_sqm') or None,
            amount=request.POST['amount'],
            effective_from=request.POST['effective_from'],
        )
        messages.success(request, 'Levy rate added.')
        return redirect('web:levy_rates')
    return render(request, 'web/levies/rate_form.html', {'pending_count': pending_count(request)})


# ── MAINTENANCE ───────────────────────────────────────────────────────────────

@login_required
def maintenance_list(request):
    from apps.maintenance.models import MaintenanceRequest
    estate, role = get_estate_and_role(request)
    qs = MaintenanceRequest.objects.filter(estate=estate).select_related('unit', 'reported_by', 'assigned_to') if estate else []
    if role == 'resident':
        from apps.residents.models import Resident
        resident = Resident.objects.filter(estate=estate, user=request.user).first()
        if resident:
            qs = qs.filter(reported_by=resident)
    return render(request, 'web/maintenance/list.html', {'requests': qs, 'pending_count': pending_count(request)})


@login_required
def maintenance_detail(request, pk):
    from apps.maintenance.models import MaintenanceRequest, MaintenanceComment
    estate, role = get_estate_and_role(request)
    req      = get_object_or_404(MaintenanceRequest, pk=pk, estate=estate)
    comments = req.comments.filter(is_internal=False) if role == 'resident' else req.comments.all()
    return render(request, 'web/maintenance/detail.html', {'req': req, 'comments': comments, 'role': role, 'pending_count': pending_count(request)})


@login_required
def maintenance_add(request):
    from apps.maintenance.models import MaintenanceRequest
    from apps.residents.models import Resident, Unit
    estate, role = get_estate_and_role(request)
    if request.method == 'POST':
        unit = get_object_or_404(Unit, id=request.POST['unit'], estate=estate)
        reporter = Resident.objects.filter(estate=estate, user=request.user).first()
        MaintenanceRequest.objects.create(
            estate=estate,
            unit=unit,
            reported_by=reporter,
            title=request.POST['title'],
            description=request.POST.get('description', ''),
            category=request.POST.get('category', 'general'),
            priority=request.POST.get('priority', 'medium'),
        )
        messages.success(request, 'Maintenance request submitted.')
        return redirect('web:maintenance')
    units = Unit.objects.filter(estate=estate)
    return render(request, 'web/maintenance/form.html', {'units': units, 'pending_count': pending_count(request)})


# ── VISITORS ──────────────────────────────────────────────────────────────────

@login_required
def visitors_list(request):
    from apps.visitors.models import GateLog, VisitorPreRegistration
    from apps.residents.models import Resident
    estate, role = get_estate_and_role(request)
    today = timezone.now().date()
    gate_logs        = GateLog.objects.filter(estate=estate, entry_time__date=today).select_related('host_resident').order_by('-entry_time') if estate else []
    visitors_inside  = GateLog.objects.filter(estate=estate, exit_time__isnull=True).select_related('host_resident') if estate else []
    pre_registrations = VisitorPreRegistration.objects.filter(estate=estate, is_used=False).order_by('expected_arrival') if estate else []
    residents = Resident.objects.filter(estate=estate, is_active=True).select_related('unit')
    return render(request, 'web/visitors/list.html', {
        'gate_logs': gate_logs, 'visitors_inside': visitors_inside,
        'pre_registrations': pre_registrations, 'residents': residents,
        'pending_count': pending_count(request),
    })


@require_POST
@login_required
def visitor_entry(request):
    from apps.visitors.models import GateLog, VisitorPreRegistration
    from apps.residents.models import Resident
    estate, role = get_estate_and_role(request)
    access_code = request.POST.get('access_code', '').strip()
    pre_reg = None
    if access_code:
        pre_reg = VisitorPreRegistration.objects.filter(estate=estate, access_code=access_code).first()
        if pre_reg and pre_reg.is_valid:
            pre_reg.is_used = True
            pre_reg.save()

    host_id = request.POST.get('host_resident')
    host    = Resident.objects.filter(id=host_id, estate=estate).first() if host_id else None
    GateLog.objects.create(
        estate=estate,
        visitor_name=request.POST['visitor_name'],
        visitor_id_number=request.POST.get('visitor_id_number', ''),
        vehicle_registration=request.POST.get('vehicle_registration', ''),
        host_resident=host,
        security_officer=request.user,
        pre_registration=pre_reg,
    )
    messages.success(request, f"{request.POST['visitor_name']} logged in successfully.")
    return redirect('web:visitors')


@require_POST
@login_required
def visitor_exit(request, pk):
    from apps.visitors.models import GateLog
    estate, role = get_estate_and_role(request)
    log = get_object_or_404(GateLog, pk=pk, estate=estate)
    log.log_exit()
    messages.success(request, f'{log.visitor_name} has exited.')
    return redirect('web:visitors')


@require_POST
@login_required
def visitor_preregister(request):
    from apps.visitors.models import VisitorPreRegistration
    from apps.residents.models import Resident
    estate, role = get_estate_and_role(request)
    resident_id = request.POST.get('resident')
    resident    = Resident.objects.filter(id=resident_id, estate=estate).first() if resident_id else None
    pre = VisitorPreRegistration.objects.create(
        estate=estate,
        resident=resident,
        visitor_name=request.POST['visitor_name'],
        visitor_phone=request.POST.get('visitor_phone', ''),
        expected_arrival=request.POST['expected_arrival'],
        purpose=request.POST.get('purpose', ''),
    )
    messages.success(request, f'Visitor pre-registered. Access code: {pre.access_code}')
    return redirect('web:visitors')


# ── ANNOUNCEMENTS ─────────────────────────────────────────────────────────────

@login_required
def announcements_list(request):
    from apps.announcements.models import Announcement
    estate, role = get_estate_and_role(request)
    qs = Announcement.objects.filter(estate=estate).order_by('-created_at') if estate else []
    if role == 'resident':
        qs = qs.filter(is_published=True)
    return render(request, 'web/announcements/list.html', {'announcements': qs, 'pending_count': pending_count(request)})


@login_required
def announcement_add(request):
    from apps.announcements.models import Announcement
    estate, role = get_estate_and_role(request)
    if request.method == 'POST':
        ann = Announcement.objects.create(
            estate=estate,
            created_by=request.user,
            title=request.POST['title'],
            body=request.POST['body'],
            category=request.POST.get('category', 'general'),
            send_email='send_email' in request.POST,
        )
        if 'publish_now' in request.POST:
            ann.publish()
            messages.success(request, 'Announcement published.')
        else:
            messages.success(request, 'Announcement saved as draft.')
        return redirect('web:announcements')
    return render(request, 'web/announcements/form.html', {'pending_count': pending_count(request)})


# ── PENDING REGISTRATIONS ─────────────────────────────────────────────────────

@login_required
def pending_registrations(request):
    estate, role = get_estate_and_role(request)
    if role not in ['superadmin', 'estate_admin', 'estate_manager']:
        return redirect('web:dashboard')
    pending = EstateMembership.objects.filter(
        estate=estate,
        status='pending'       # ← only pending, rejected are excluded automatically
    ).select_related('user').order_by('joined_at') if estate else []
    return render(request, 'web/auth/pending.html', {
        'pending': pending,
        'pending_count': len(list(pending))
    })


@require_POST
@login_required
@require_POST
@login_required
def approve_registration(request, membership_id, action):
    estate, role = get_estate_and_role(request)
    membership = get_object_or_404(EstateMembership, id=membership_id, estate=estate)

    if action == 'approve':
        membership.approve(request.user)
        from apps.notifications.tasks import notify_registration_approved
        notify_registration_approved(membership.user.id, membership.estate.id)
        messages.success(request, f'{membership.user.get_full_name()} has been approved.')

    elif action == 'reject':
        reason      = request.POST.get('reason', '').strip()
        rejected_user  = membership.user
        full_name    = rejected_user.get_full_name()
        user_id      = rejected_user.id
        estate_id    = membership.estate.id

    # Send email BEFORE deleting so we still have the user data
    from apps.notifications.tasks import notify_registration_rejected
    notify_registration_rejected(user_id, estate_id, reason)

    # Delete the user entirely — cascades to membership too
    rejected_user.delete()

    messages.warning(request, f'{full_name} has been rejected and removed.')

    return redirect('web:pending_registrations')


# ── INVITES ───────────────────────────────────────────────────────────────────

@login_required
def invites_list(request):
    estate, role = get_estate_and_role(request)
    if role not in ['superadmin', 'estate_admin', 'estate_manager']:
        return redirect('web:dashboard')
    invites = EstateInvite.objects.filter(estate=estate).order_by('-created_at') if estate else []
    return render(request, 'web/auth/invites.html', {'invites': invites, 'pending_count': pending_count(request)})


@require_POST
@login_required
def invite_create(request):
    estate, role = get_estate_and_role(request)
    expires_at = request.POST.get('expires_at')
    EstateInvite.objects.create(
        estate=estate,
        created_by=request.user,
        role=request.POST.get('role', 'resident'),
        max_uses=request.POST.get('max_uses') or 1,
        expires_at=expires_at if expires_at else None,
    )
    messages.success(request, 'Invite link created.')
    return redirect('web:invites')


@require_POST
@login_required
def invite_deactivate(request, pk):
    estate, role = get_estate_and_role(request)
    invite = get_object_or_404(EstateInvite, pk=pk, estate=estate)
    invite.is_active = False
    invite.save()
    messages.success(request, 'Invite deactivated.')
    return redirect('web:invites')


# ── PROFILE ───────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name', user.last_name)
        user.email      = request.POST.get('email', user.email)
        user.phone      = request.POST.get('phone', user.phone)
        new_password    = request.POST.get('new_password', '').strip()
        if new_password:
            if not user.check_password(request.POST.get('old_password', '')):
                messages.error(request, 'Current password is incorrect.')
                return redirect('web:profile')
            user.set_password(new_password)
        user.save()
        messages.success(request, 'Profile updated.')
        if new_password:
            login(request, user)
    memberships = EstateMembership.objects.filter(user=request.user, is_active=True).select_related('estate')
    return render(request, 'web/auth/profile.html', {'memberships': memberships, 'pending_count': pending_count(request)})
