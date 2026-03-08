from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, EstateMembership, EstateInvite


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled.")
        if user.status == "pending":
            raise serializers.ValidationError(
                "Your account is pending approval. "
                "You will receive an email once approved."
            )
        if user.status == "rejected":
            raise serializers.ValidationError(
                "Your registration was not approved. "
                "Please contact the estate manager."
            )
        data["user"] = user
        return data


class SelfRegisterSerializer(serializers.ModelSerializer):
    """
    Used on the public registration page.
    Accepts an optional invite_code for auto-approval.
    """
    password    = serializers.CharField(write_only=True, min_length=8)
    password2   = serializers.CharField(write_only=True, label="Confirm password")
    invite_code = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Optional invite code from your estate manager"
    )
    unit_number = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Your unit number (e.g. A101)"
    )
    estate_slug = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Estate identifier — provided by your manager"
    )

    class Meta:
        model  = User
        fields = [
            "username", "email", "first_name", "last_name",
            "phone", "password", "password2",
            "invite_code", "unit_number", "estate_slug",
        ]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        invite_code = data.get("invite_code")
        estate_slug = data.get("estate_slug")

        # Validate invite code if provided
        if invite_code:
            try:
                invite = EstateInvite.objects.select_related("estate").get(code=invite_code)
                if not invite.is_valid:
                    raise serializers.ValidationError(
                        {"invite_code": "This invite link has expired or is no longer valid."}
                    )
                data["_invite"] = invite
            except EstateInvite.DoesNotExist:
                raise serializers.ValidationError(
                    {"invite_code": "Invalid invite code."}
                )

        # Validate estate slug if provided without invite
        elif estate_slug:
            from apps.estates.models import Estate
            try:
                estate = Estate.objects.get(slug=estate_slug, is_active=True)
                data["_estate"] = estate
            except Estate.DoesNotExist:
                raise serializers.ValidationError(
                    {"estate_slug": "Estate not found. Please check with your manager."}
                )

        return data

    def create(self, validated_data):
        # Pull out non-model fields
        validated_data.pop("password2")
        password    = validated_data.pop("password")
        invite      = validated_data.pop("_invite",      None)
        estate      = validated_data.pop("_estate",      None)
        invite_code = validated_data.pop("invite_code",  None)
        unit_number = validated_data.pop("unit_number",  "")
        estate_slug = validated_data.pop("estate_slug",  "")

        # Determine approval status
        if invite:
            # Auto-approve — came via valid invite link
            validated_data["status"]    = "approved"
            validated_data["is_active"] = True
            estate = invite.estate
        else:
            # Needs manual approval
            validated_data["status"]    = "pending"
            validated_data["is_active"] = False

        # Create the user
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Create estate membership
        if invite:
            EstateMembership.objects.create(
                user        = user,
                estate      = estate,
                role        = invite.role,
                status      = "approved",
                is_active   = True,
                unit_number = unit_number,
                approved_at = timezone.now(),
            )
            invite.use()

            # Notify managers of new auto-approved member
            from apps.notifications.tasks import notify_new_member
            notify_new_member(user.id, estate.id, auto_approved=True)

        elif estate:
            # Pending approval — create membership as pending
            EstateMembership.objects.create(
                user        = user,
                estate      = estate,
                role        = "resident",
                status      = "pending",
                is_active   = False,
                unit_number = unit_number,
            )
            # Notify managers to review
            from apps.notifications.tasks import notify_pending_registration
            notify_pending_registration(user.id, estate.id)

        return user


class PendingRegistrationSerializer(serializers.ModelSerializer):
    """Used by managers to view pending registrations."""
    membership_id  = serializers.SerializerMethodField()
    estate_name    = serializers.SerializerMethodField()
    unit_number    = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ["id", "username", "email", "first_name", "last_name",
                  "phone", "status", "membership_id", "estate_name",
                  "unit_number", "date_joined"]

    def get_membership_id(self, obj):
        membership = self._get_membership(obj)
        return membership.id if membership else None

    def get_estate_name(self, obj):
        membership = self._get_membership(obj)
        return membership.estate.name if membership else None

    def get_unit_number(self, obj):
        membership = self._get_membership(obj)
        return membership.unit_number if membership else None

    def _get_membership(self, obj):
        estate = self.context.get("estate")
        if estate:
            return obj.estate_memberships.filter(estate=estate).first()
        return obj.estate_memberships.first()


class EstateInviteSerializer(serializers.ModelSerializer):
    invite_url  = serializers.SerializerMethodField()
    estate_name = serializers.CharField(source="estate.name", read_only=True)

    class Meta:
        model  = EstateInvite
        fields = ["id", "estate", "estate_name", "code", "role",
                  "max_uses", "times_used", "expires_at",
                  "is_active", "is_valid", "invite_url", "created_at"]
        read_only_fields = ["id", "code", "times_used", "created_at"]

    def get_invite_url(self, obj):
        request = self.context.get("request")
        if request:
            return f"{request.scheme}://{request.get_host()}/register?invite={obj.code}"
        return f"/register?invite={obj.code}"


class UserSerializer(serializers.ModelSerializer):
    memberships = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ["id", "username", "email", "first_name", "last_name",
                  "phone", "avatar", "status", "memberships"]
        read_only_fields = ["id", "status"]

    def get_memberships(self, obj):
        return EstateMembership.objects.filter(
            user=obj, is_active=True
        ).values("estate__name", "estate__slug", "role")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class EstateMembershipSerializer(serializers.ModelSerializer):
    estate_name = serializers.CharField(source="estate.name", read_only=True)
    estate_slug = serializers.CharField(source="estate.slug", read_only=True)
    user_name   = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email  = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model  = EstateMembership
        fields = ["id", "user", "user_name", "user_email", "estate",
                  "estate_name", "estate_slug", "role", "status",
                  "is_active", "unit_number", "joined_at", "approved_at"]
        read_only_fields = ["id", "joined_at", "approved_at"]