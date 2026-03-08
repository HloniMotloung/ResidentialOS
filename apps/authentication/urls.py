from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, LogoutView, SelfRegisterView,
    ValidateInviteView, PendingRegistrationsView,
    ApproveRegistrationView, EstateInviteView,
    EstateInviteDetailView, MeView,
    ChangePasswordView, EstateMembershipListView,
)

urlpatterns = [
    # Public
    path("login/",              LoginView.as_view(),           name="auth-login"),
    path("logout/",             LogoutView.as_view(),           name="auth-logout"),
    path("register/",           SelfRegisterView.as_view(),     name="auth-register"),
    path("refresh/",            TokenRefreshView.as_view(),     name="auth-refresh"),
    path("invite/<str:code>/",  ValidateInviteView.as_view(),   name="auth-invite-validate"),

    # Authenticated
    path("me/",                 MeView.as_view(),               name="auth-me"),
    path("change-password/",    ChangePasswordView.as_view(),   name="auth-change-password"),
    path("memberships/",        EstateMembershipListView.as_view(), name="auth-memberships"),

    # Manager only
    path("pending/",            PendingRegistrationsView.as_view(), name="auth-pending"),
    path("pending/<int:membership_id>/<str:action>/",
         ApproveRegistrationView.as_view(),                     name="auth-approve"),
    path("invites/",            EstateInviteView.as_view(),     name="auth-invites"),
    path("invites/<int:pk>/",   EstateInviteDetailView.as_view(), name="auth-invite-detail"),
]