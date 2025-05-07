from django.db import models
from django.conf import settings
from django.utils import timezone

class Recipe(models.Model):
    CATEGORY_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('non-vegetarian', 'Non-Vegetarian'),
        ('soups', 'Soups'),
        ('desserts', 'Desserts'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    ingredients = models.TextField()
    instructions = models.TextField()
    cooking_time = models.IntegerField(help_text="Cooking time in minutes", null=True, blank=True)
    image = models.ImageField(upload_to='recipe_images/', null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recipes', null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(null=True, blank=True, help_text="Admin notes on approval/rejection")

    # --- Translation-related fields ---
    is_translation = models.BooleanField(default=False)
    original_recipe = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='translations')
    language = models.CharField(max_length=10, default='en')  # Default to English

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

    def total_likes(self):
        return self.likes.count()
    
    def total_comments(self):
        return self.comments.count()
    
    def is_approved(self):
        return self.status == 'approved'

    # --- Translation methods ---
    def get_translation(self, language_code):
        """
        Get the recipe translated to the specified language.
        If translation doesn't exist, return None.
        """
        translation = self.translations.filter(language=language_code).first()
        return translation

    def get_or_create_translation(self, language_code):
        """
        Get existing translation or translate recipe to specified language.
        """
        existing = self.get_translation(language_code)
        if existing:
            return existing
        from .utils import translate_recipe
        translated_data = translate_recipe(self, language_code)
        if translated_data:
            translation = Recipe.objects.create(
                title=translated_data['title'],
                description=translated_data['description'],
                ingredients=translated_data['ingredients'],
                instructions=translated_data['instructions'],
                is_translation=True,
                original_recipe=self,
                language=language_code,
                # Copy other fields as needed (e.g., image, cooking_time, etc.)
            )
            return translation
        return None

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'recipe')

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

class EmojiReaction(models.Model):
    EMOJI_CHOICES = [
        ('👍', 'Thumbs Up'),
        ('❤️', 'Heart'),
        ('😋', 'Yummy'),
        ('👏', 'Clap'),
        ('🔥', 'Fire'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='emoji_reactions')
    emoji = models.CharField(max_length=2, choices=EMOJI_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'recipe', 'emoji')
    def __str__(self):
        return f"{self.user.username} reacted with {self.emoji} on {self.recipe.title}"

# --- New model for user language preference ---
class UserLanguagePreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    language = models.CharField(max_length=10, default='en')  # Default to English

    def __str__(self):
        return f"{self.user.username} - {self.language}"
