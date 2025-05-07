from django.core.management.base import BaseCommand
from django.db.models import Q
from RecipesApp.models import Recipe
from RecipesApp.utils import translate_recipe
import time

class Command(BaseCommand):
    """Batch translates recipes"""
    help = 'Batch translate recipes to specified language'

    def add_arguments(self, parser):
        parser.add_argument('language', type=str, help='Target language code (e.g., es, fr)')
        parser.add_argument('--limit', type=int, default=10, help='Max number of recipes to translate')
        parser.add_argument('--delay', type=float, default=1.0, help='Delay between API calls in seconds')

    def handle(self, *args, **kwargs):
        language_code = kwargs['language']
        limit = kwargs['limit']
        delay = kwargs['delay']
        
        # Get original recipes that don't have translations in target language
        recipes = Recipe.objects.filter(
            is_translation=False
        ).exclude(
            translations__language=language_code
        )[:limit]
        
        self.stdout.write(f"Found {recipes.count()} recipes to translate to {language_code}")
        
        success_count = 0
        error_count = 0
        
        for recipe in recipes:
            self.stdout.write(f"Translating recipe: {recipe.title} (ID: {recipe.id})")
            
            try:
                # Attempt to translate
                translated = recipe.get_or_create_translation(language_code)
                
                if translated:
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Translated: {translated.title} (ID: {translated.id})"
                    ))
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(
                        f"✗ Translation failed for recipe ID: {recipe.id}"
                    ))
                
                # Add delay to avoid rate limiting
                time.sleep(delay)
                
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f"✗ Error translating recipe ID {recipe.id}: {str(e)}"
                ))
        
        self.stdout.write(f"Translation completed. Successes: {success_count}, Errors: {error_count}")
