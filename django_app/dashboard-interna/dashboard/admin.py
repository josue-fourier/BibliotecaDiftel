from django.contrib import admin
from .models import USMUser, InitialProject, ProjectImage

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
