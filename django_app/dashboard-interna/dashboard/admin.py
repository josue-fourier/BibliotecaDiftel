from django.contrib import admin
from .models import (
    USMUser,
    InitialProject,
    ProjectImage,
    Workshop,
    WorkshopImage,
    CommunityMember,
)

admin.site.register(USMUser)

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1

@admin.register(InitialProject)
class InitialProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'generation', 'created_at')
    list_filter = ('generation',)
    search_fields = ('title', 'members', 'description')
    inlines = [ProjectImageInline]


class WorkshopImageInline(admin.TabularInline):
    model = WorkshopImage
    extra = 1
    fields = ('image', 'order', 'caption')
    ordering = ('order',)


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'event_type', 'guia_url', 'created_at')
    list_filter = ('year', 'event_type')
    search_fields = ('title', 'description', 'guia_url')
    inlines = [WorkshopImageInline]


@admin.register(CommunityMember)
class CommunityMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'generation', 'current_role', 'email')
    list_filter = ('generation',)
    search_fields = ('name', 'bio', 'current_role', 'email')

