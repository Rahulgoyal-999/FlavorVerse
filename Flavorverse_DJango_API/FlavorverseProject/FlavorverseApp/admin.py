from django.contrib import admin
from django.contrib.auth.models import User
from .models import NewsletterSubscriber, APIKey, ContactMessage
from django.utils.html import format_html

# Register your models here.
admin.site.register(NewsletterSubscriber)
admin.site.register(APIKey)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'message_preview', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_filter = ('created_at',)
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at', 'flask_id')
    date_hierarchy = 'created_at'
    fields = ('name', 'email', 'subject', 'message', 'created_at', 'flask_id')
    
    def message_preview(self, obj):
        """Display a truncated version of the message in the list view"""
        if obj.message:
            return obj.message if len(obj.message) <= 50 else f"{obj.message[:47]}..."
        return "-"
    message_preview.short_description = "Message"
    
    def has_add_permission(self, request):
        # Messages should only be added through the contact form
        return False
    
    def has_change_permission(self, request, obj=None):
        # Messages shouldn't be editable
        return False
