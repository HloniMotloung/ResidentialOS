from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EstateMembership, EstateInvite


# ── MEMBERSHIP INLINE ─────────────────────────────────────────────────────────

class EstateMembershipInline(admin.TabularInline):
    model           = EstateMembership
    fk_name         = "user"
    extra           = 0
    readonly_fields = ['joined_at', 'approved_at', 'approved_by']
    fields          = ['estate', 'role', 'status', 'is_active', 'unit_number', 'joined_at']


# ── BASE USER ADMIN ────────────────────────────────────────────────────────────

class BaseFilteredUserAdmin(BaseUserAdmin):
    inlines         = [EstateMembershipInline]
    list_display    = ['username', 'email', 'first_name', 'last_name', 'phone', 'status', 'is_active']
    list_filter     = ['status', 'is_active']
    search_fields   = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering        = ['first_name', 'last_name']
    readonly_fields = ['last_login', 'date_joined', 'approved_at', 'approved_by']

    fieldsets = (
        (None,            {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')}),
        ('Status',        {'fields': ('status', 'approved_by', 'approved_at', 'notes')}),
        ('Permissions',   {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates',         {'fields': ('last_login', 'date_joined')}),
    )

    def get_queryset(self, request):
        # Exclude users rejected at the User level
        return super().get_queryset(request).exclude(status='rejected')


# ── 1. ADMIN / STAFF USERS ────────────────────────────────────────────────────

class AdminUserAdmin(BaseFilteredUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone', 'is_superuser', 'is_staff']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)


# ── 2. ESTATE MEMBERS (managers, security) ────────────────────────────────────

class EstateMemberUserAdmin(BaseFilteredUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone', 'status', 'get_role']
    list_filter  = ['status', 'is_active']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            is_staff=False,
            estate_memberships__role__in=['estate_admin', 'estate_manager', 'security'],
            estate_memberships__status__in=['pending', 'approved'],
        ).distinct()

    @admin.display(description='Role')
    def get_role(self, obj):
        m = obj.estate_memberships.filter(
            role__in=['estate_admin', 'estate_manager', 'security'],
            status__in=['pending', 'approved'],
        ).first()
        return m.get_role_display() if m else 'Unknown'


# ── 3. RESIDENTS / TENANTS ────────────────────────────────────────────────────

class ResidentUserAdmin(BaseFilteredUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone', 'status', 'get_unit']
    list_filter  = ['status', 'is_active']

    def get_queryset(self, request):
        # Exclude users whose resident membership is rejected
        return super().get_queryset(request).filter(
            is_staff=False,
            estate_memberships__role='resident',
            estate_memberships__status__in=['pending', 'approved'],
        ).distinct()

    @admin.display(description='Unit')
    def get_unit(self, obj):
        m = obj.estate_memberships.filter(
            role='resident',
            status__in=['pending', 'approved'],
        ).first()
        return m.unit_number if m and m.unit_number else 'No unit'


# ── PROXY MODELS ──────────────────────────────────────────────────────────────

class AdminUser(User):
    class Meta:
        proxy               = True
        verbose_name        = 'Admin / Staff User'
        verbose_name_plural = 'Admin & Staff Users'


class EstateMemberUser(User):
    class Meta:
        proxy               = True
        verbose_name        = 'Estate Member'
        verbose_name_plural = 'Estate Members (Managers & Security)'


class ResidentUser(User):
    class Meta:
        proxy               = True
        verbose_name        = 'Resident / Tenant'
        verbose_name_plural = 'Residents & Tenants'


class AccessLogMembership(EstateMembership):
    class Meta:
        proxy               = True
        verbose_name        = 'Access Log Entry'
        verbose_name_plural = 'Access Log'


# ── REGISTER ──────────────────────────────────────────────────────────────────

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

admin.site.register(AdminUser,        AdminUserAdmin)
admin.site.register(EstateMemberUser, EstateMemberUserAdmin)
admin.site.register(ResidentUser,     ResidentUserAdmin)
admin.site.register(EstateInvite)


@admin.register(EstateMembership)
class EstateMembershipAdmin(admin.ModelAdmin):
    list_display    = ['user', 'estate', 'role', 'status', 'is_active', 'unit_number', 'joined_at']
    list_filter     = ['status', 'role', 'is_active']
    search_fields   = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['joined_at', 'approved_at']

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(status='rejected')


@admin.register(AccessLogMembership)
class AccessLogAdmin(admin.ModelAdmin):
    """
    Read-only audit log of ALL membership actions including rejections.
    Visible to staff and superusers only — estate managers cannot see this.
    """
    list_display  = [
        'get_full_name', 'get_email', 'estate', 'role',
        'status', 'unit_number', 'joined_at', 'approved_by', 'approved_at', 'notes',
    ]
    list_filter   = ['status', 'role', 'estate']
    search_fields = [
        'user__username', 'user__email',
        'user__first_name', 'user__last_name',
        'approved_by__username',
    ]
    readonly_fields = [
        'user', 'estate', 'role', 'status', 'is_active',
        'unit_number', 'joined_at', 'approved_by', 'approved_at', 'notes',
    ]
    ordering = ['-joined_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_perms(self, request):
        return request.user.is_staff or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff or request.user.is_superuser

    # Full audit trail — includes rejected, pending, approved
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'estate', 'approved_by')

    @admin.display(description='Name', ordering='user__first_name')
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description='Email', ordering='user__email')
    def get_email(self, obj):
        return obj.user.email