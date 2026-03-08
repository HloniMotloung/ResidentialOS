from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    # Auth
    path('',                                    views.login_view,            name='login'),
    path('register/',                           views.register_view,         name='register'),
    path('logout/',                             views.logout_view,           name='logout'),
    path('profile/',                            views.profile,               name='profile'),

    # Dashboard
    path('dashboard/',                          views.dashboard,             name='dashboard'),

    # Residents
    path('residents/',                          views.residents_list,        name='residents'),
    path('residents/add/',                      views.resident_add,          name='resident_add'),
    path('residents/<int:pk>/',                 views.resident_detail,       name='resident_detail'),
    path('residents/<int:pk>/edit/',            views.resident_edit,         name='resident_edit'),

    # Units
    path('units/',                              views.units_list,            name='units'),
    path('units/add/',                          views.unit_add,              name='unit_add'),

    # Levies
    path('levies/',                             views.levies_list,           name='levies'),
    path('levies/add/',                         views.levy_add,              name='levy_add'),
    path('levies/<int:pk>/',                    views.levy_detail,           name='levy_detail'),
    path('levies/<int:pk>/payment/',            views.levy_payment,          name='levy_payment'),
    path('levies/rates/',                       views.levy_rates,            name='levy_rates'),
    path('levies/rates/add/',                   views.levy_rate_add,         name='levy_rate_add'),

    # Maintenance
    path('maintenance/',                        views.maintenance_list,      name='maintenance'),
    path('maintenance/add/',                    views.maintenance_add,       name='maintenance_add'),
    path('maintenance/<int:pk>/',               views.maintenance_detail,    name='maintenance_detail'),

    # Visitors
    path('visitors/',                           views.visitors_list,         name='visitors'),
    path('visitors/entry/',                     views.visitor_entry,         name='visitor_entry'),
    path('visitors/<int:pk>/exit/',             views.visitor_exit,          name='visitor_exit'),
    path('visitors/preregister/',               views.visitor_preregister,   name='visitor_preregister'),

    # Announcements
    path('announcements/',                      views.announcements_list,    name='announcements'),
    path('announcements/add/',                  views.announcement_add,      name='announcement_add'),

    # Access management
    path('pending/',                            views.pending_registrations, name='pending_registrations'),
    path('pending/<int:membership_id>/<str:action>/', views.approve_registration, name='approve_registration'),
    path('invites/',                            views.invites_list,          name='invites'),
    path('invites/create/',                     views.invite_create,         name='invite_create'),
    path('invites/<int:pk>/deactivate/',        views.invite_deactivate,     name='invite_deactivate'),
]
