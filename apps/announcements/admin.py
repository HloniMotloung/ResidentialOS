from django.contrib import admin
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display  = ["title", "category", "is_published", "published_at", "estate"]
    list_filter   = ["category", "is_published", "estate"]
    search_fields = ["title", "body"]