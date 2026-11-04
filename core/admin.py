from django.contrib import admin
from .models import Profile, Assignment, AttestationApplication, ChecklistItem, EvidenceDocument

class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0

@admin.register(AttestationApplication)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "assignment", "goal", "category", "status", "updated_at")
    list_filter = ("goal", "category", "status")
    search_fields = ("user__username", "user__last_name", "assignment__position")

@admin.register(ChecklistItem)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ("title", "scope", "required", "active", "sort_order")
    list_editable = ("required", "active", "sort_order")
    list_filter = ("scope", "active")

admin.site.register(Profile)
admin.site.register(Assignment)
admin.site.register(EvidenceDocument)
