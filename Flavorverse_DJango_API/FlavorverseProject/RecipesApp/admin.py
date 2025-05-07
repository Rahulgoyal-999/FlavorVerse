from django.contrib import admin
from .models import Recipe, Like, Comment, EmojiReaction

class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_at', 'status')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    list_editable = ('status',)
    actions = ['approve_recipes', 'reject_recipes']
    list_per_page = 20
    
    def approve_recipes(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f"{queryset.count()} recipes have been approved.")
    approve_recipes.short_description = "Approve selected recipes"
    
    def reject_recipes(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f"{queryset.count()} recipes have been rejected.")
    reject_recipes.short_description = "Reject selected recipes"

@admin.register(EmojiReaction)
class EmojiReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'emoji', 'created_at')
    list_filter = ('emoji', 'created_at')
    search_fields = ('user__username', 'recipe__title')
    list_per_page = 20

admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Like)
admin.site.register(Comment)
