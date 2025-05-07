from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Recipe
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .forms import RecipeForm, CommentForm
from .models import Recipe, Like, Comment, EmojiReaction, UserLanguagePreference
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils import get_language_name
from django.utils import timezone
import requests



def view_all_recipes_view(request):
    # Get category filter from query parameters
    category = request.GET.get('category', None)
    
    # Base queryset with only approved recipes
    base_queryset = Recipe.objects.filter(status='approved')
    
    # Filter recipes based on category if provided
    if category and category.lower() != 'all':
        recipes_list = base_queryset.filter(category=category.lower()).order_by('-created_at')
    else:
        recipes_list = base_queryset.order_by('-created_at')
    
    # Set up pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(recipes_list, 9)  # Show 9 recipes per page
    
    try:
        recipes = paginator.page(page)
    except PageNotAnInteger:
        recipes = paginator.page(1)
    except EmptyPage:
        recipes = paginator.page(paginator.num_pages)
    
    # Get the current active category for highlighting the filter button
    active_category = category if category else 'all'
    
    context = {
        'recipes': recipes,
        'active_category': active_category
    }
    
    return render(request, "allrecipes.html", context)

@login_required
def add_your_recipe_view(request):
    if request.method == 'POST':
        try:
            # Validate required fields
            title = request.POST.get('title')
            ingredients = request.POST.get('ingredients')
            instructions = request.POST.get('instructions')
            category = request.POST.get('category')
            
            if not all([title, ingredients, instructions, category]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'addyourrecipe.html')
            
            # Validate ingredients format - make sure there are enough segments (at least 3 ingredients)
            ingredients_lines = [line.strip() for line in ingredients.splitlines() if line.strip()]
            if len(ingredients_lines) < 3:
                messages.error(request, 'API Error: Your recipe format is incorrect. Please ensure you have at least 3 ingredients and 2 instruction steps, each on a separate line.')
                return render(request, 'addyourrecipe.html')
            
            # Validate instructions format - make sure there are enough segments (at least 2 steps)
            instructions_lines = [line.strip() for line in instructions.splitlines() if line.strip()]
            if len(instructions_lines) < 2:
                messages.error(request, 'API Error: Your recipe format is incorrect. Please ensure you have at least 3 ingredients and 2 instruction steps, each on a separate line.')
                return render(request, 'addyourrecipe.html')
            
            # Format ingredients and instructions properly
            ingredients = "\n".join(ingredients_lines)
            instructions = "\n".join(instructions_lines)
            
            description = request.POST.get('description', '')
            cooking_time = request.POST.get('cooking_time')
            if cooking_time and cooking_time.isdigit():
                cooking_time = int(cooking_time)
            else:
                cooking_time = None
            
            # Get Flask authentication token from session
            flask_token = request.session.get('flask_token')
            if not flask_token:
                messages.error(request, 'Authentication error. Please log in again.')
                return redirect('login')
            
            # Prepare recipe data for Flask API
            recipe_data = {
                'title': title,
                'ingredients': ingredients,
                'instructions': instructions,
                'category': category,
                'description': description,
                'cooking_time': cooking_time,
                'user_id': request.user.id
            }
            
            # Add image handling if needed
            image_url = ''
            if 'image' in request.FILES:
                # Here you would handle image upload to Flask or store locally
                # For simplicity, we're just noting that an image was provided
                image_url = 'placeholder_for_image_handling'
                recipe_data['image_url'] = image_url
            
            # Call Flask API to create recipe
            try:
                # Print debugging information
                print(f"DEBUG - Recipe data: {recipe_data}")
                print(f"DEBUG - Flask token: {flask_token[:10]}...")
                
                response = requests.post(
                    'http://127.0.0.1:5000/api/recipes',
                    json=recipe_data,
                    headers={'Authorization': f'Bearer {flask_token}'},
                    timeout=10
                )
                
                # Print response for debugging
                print(f"DEBUG - API Response status: {response.status_code}")
                print(f"DEBUG - API Response text: {response.text[:200]}")
                
                # Check response
                if response.status_code == 201:  # Created
                    api_response = response.json()
                    if api_response.get('success'):
                        messages.success(request, 'Recipe submitted successfully! It is now pending approval by an administrator.')
                        return redirect('my_pending_recipes')
                    else:
                        messages.error(request, f"API Error: {api_response.get('message', 'Unknown error')}")
                elif response.status_code == 422:
                    api_response = response.json()
                    messages.error(request, f"API Error: {api_response.get('message', 'Validation failed.')}")
                    return render(request, 'addyourrecipe.html')
                elif response.status_code == 401:  # Unauthorized
                    messages.error(request, 'Authentication error. Please log in again.')
                    # Clear Flask token as it might be invalid
                    request.session['flask_token'] = None
                    request.session.modified = True
                    return redirect('login')
                else:
                    messages.error(request, f'API Error: {response.status_code} - {response.text}')
            except requests.RequestException as e:
                # Handle API connection error - DO NOT SAVE LOCALLY
                print(f"Flask API connection error: {str(e)}. Not saving locally.")
                messages.error(request, 'Recipe not saved! API connection failed. Please try again later.')
                return render(request, 'addyourrecipe.html')
                
        except Exception as e:
            messages.error(request, f'Error adding recipe: {str(e)}')
            return render(request, 'addyourrecipe.html')

    # Clear any existing messages when loading the form
    storage = messages.get_messages(request)
    storage.used = True
    
    return render(request, 'addyourrecipe.html')


def added_recipe_view(request):
    # Get the recipe title from session
    recipe_title = request.session.get('recipe_title', '')
    
    # Clear the session after getting the title
    if 'recipe_title' in request.session:
        del request.session['recipe_title']
    
    context = {
        'title': recipe_title
    }
    return render(request, "recipe_added.html", context)


def all_added_recipes_view(request):
    user_recipes = []
    
    if request.user.is_authenticated:
        # Get Flask authentication token from session
        flask_token = request.session.get('flask_token')
        user_email = request.session.get('user_email')
        user_data = request.session.get('user_data', {})
        user_id = user_data.get('id')
        
        # Try to get recipes from Flask API if we have authentication
        if flask_token and user_id:
            try:
                response = requests.get(
                    f'http://127.0.0.1:5000/api/recipes',
                    params={'user_id': user_id},
                    headers={'Authorization': f'Bearer {flask_token}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    api_response = response.json()
                    if api_response.get('success') and 'recipes' in api_response:
                        api_recipes = api_response['recipes']
                        
                        # Convert API recipes to Django model format for template compatibility
                        from django.utils.dateparse import parse_datetime
                        for recipe_data in api_recipes:
                            recipe = Recipe(
                                id=recipe_data['id'],
                                title=recipe_data['title'],
                                ingredients=recipe_data['ingredients'],
                                instructions=recipe_data['instructions'],
                                category=recipe_data['category'],
                                user_id=recipe_data['user_id'],
                                image=recipe_data.get('image_url', '')
                            )
                            user_recipes.append(recipe)
                else:
                    # If API call fails, fall back to database
                    print(f"API returned error status: {response.status_code}. Falling back to database.")
                    user_recipes = []  # Or show a message: "No recipes found. Please log in."
                    
            except requests.RequestException as e:
                # Handle API connection error
                print(f"Flask API connection error: {str(e)}. Falling back to database.")
                user_recipes = []  # Or show a message: "No recipes found. Please log in."
        else:
            # Use Django database if we don't have Flask authentication
            user_recipes = []  # Or show a message: "No recipes found. Please log in."
    
    context = {
        'recipes': user_recipes
    }
    return render(request, 'recipes.html', context)


def vegetarian_view(request):
    return render(request,"veg.html")


def non_vegetarian_view(request):
    return render(request,"nonveg.html")


def soups_view(request):
    return render(request,"soups.html")


def desserts_view(request):
    return render(request,"desserts.html")


def lettuce_wrap_view(request):
    return render(request, 'lettuce_wrap.html')


def vegan_fajitas_view(request):
    return render(request, 'vegan_fajitas.html')


def chickpea_curry(request):
    return render(request, 'chickpea_curry.html')


def scallion_roll(request):
    return render(request, 'scallion_roll.html')


def brussels_sprouts_view(request):
    return render(request, 'brussels_sprouts.html')


def scallion_pancake_view(request):
    return render(request, 'scallion_pancake.html')


def alfredo_sauce_view(request):
    return render(request, 'alfredo_sauce.html')


def sticky_gochujang_tofu_view(request):
    return render(request, 'sticky_gochujang_tofu.html')


def mississippi_pot_roast_cheesesteak_view(request):
    return render(request, 'mississippi_pot_roast_cheesesteak.html')


def baked_gnocchi_view(request):
    return render(request, 'baked_gnocchi.html')


def jalapeno_lime_chicken_view(request):
    return render(request, 'jalapeno_lime_chicken.html')


def french_silk_pie_bars_view(request):
    return render(request, 'french_silk_pie_bars.html')


def lobster_risotto_view(request):
    return render(request, 'lobster_risotto.html')


def lemon_crumb_bars_view(request):
    return render(request, 'lemon_crumb_bars.html')


@login_required
def edit_recipe_view(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id, user=request.user)
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title')
            ingredients = request.POST.get('ingredients')
            instructions = request.POST.get('instructions')
            category = request.POST.get('category')
            
            if not all([title, ingredients, instructions, category]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'edit_recipe.html', {'recipe': recipe})
            
            # Get Flask authentication token from session
            flask_token = request.session.get('flask_token')
            if not flask_token:
                messages.error(request, 'Authentication error. Please log in again.')
                return redirect('login')
            
            # Prepare recipe data for Flask API
            recipe_data = {
                'title': title,
                'ingredients': ingredients,
                'instructions': instructions,
                'category': category
            }
            
            # Handle image if provided
            if 'image' in request.FILES:
                # Here you would handle image upload to Flask or store locally
                # For simplicity, we're just noting that an image was provided
                image_url = 'placeholder_for_image_handling'
                recipe_data['image_url'] = image_url
            
            # Call Flask API to update recipe
            try:
                response = requests.put(
                    f'http://127.0.0.1:5000/api/recipes/{recipe_id}',
                    json=recipe_data,
                    headers={'Authorization': f'Bearer {flask_token}'},
                    timeout=10
                )
                
                # Check response
                if response.status_code == 200:  # OK
                    api_response = response.json()
                    if api_response.get('success'):
                        messages.success(request, 'Recipe updated successfully!')
                        return redirect('alladdedrecipespage')
                    else:
                        messages.error(request, f"API Error: {api_response.get('message', 'Unknown error')}")
                elif response.status_code == 401:  # Unauthorized
                    messages.error(request, 'Authentication error. Please log in again.')
                    # Clear Flask token as it might be invalid
                    request.session['flask_token'] = None
                    request.session.modified = True
                    return redirect('login')
                elif response.status_code == 403:  # Forbidden
                    messages.error(request, 'You do not have permission to update this recipe.')
                elif response.status_code == 404:  # Not Found
                    messages.error(request, 'Recipe not found in API. Updates will be made locally only.')
                else:
                    messages.error(request, f'API Error: {response.status_code} - {response.text}')
                    
            except requests.RequestException as e:
                # Handle API connection error - fallback to Django model
                print(f"Flask API connection error: {str(e)}. Falling back to Django model.")
                messages.warning(request, 'API connection failed. Updates will be made locally only.')
                
                # Continue with local update as fallback
                pass  # We'll continue with the Django model update below
            
            # Update Django model (either as fallback or to keep in sync with API)
            recipe.title = title
            recipe.ingredients = ingredients
            recipe.instructions = instructions
            recipe.category = category
            
            # Update image if provided
            if 'image' in request.FILES:
                recipe.image = request.FILES['image']
            
            recipe.save()
            messages.success(request, 'Recipe updated in local database.')
            return redirect('alladdedrecipespage')
            
        except Exception as e:
            messages.error(request, f'Error updating recipe: {str(e)}')
            return render(request, 'edit_recipe.html', {'recipe': recipe})
    
    return render(request, 'edit_recipe.html', {'recipe': recipe})

@login_required
def delete_recipe_view(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id, user=request.user)
    try:
        # Get Flask authentication token from session
        flask_token = request.session.get('flask_token')
        if not flask_token:
            messages.error(request, 'Authentication error. Please log in again.')
            return redirect('login')
            
        # Call Flask API to delete recipe
        try:
            response = requests.delete(
                f'http://127.0.0.1:5000/api/recipes/{recipe_id}',
                headers={'Authorization': f'Bearer {flask_token}'},
                timeout=10
            )
            
            # Check response
            if response.status_code == 200:  # OK
                api_response = response.json()
                if api_response.get('success'):
                    messages.success(request, 'Recipe deleted successfully from API!')
                else:
                    messages.error(request, f"API Error: {api_response.get('message', 'Unknown error')}")
            elif response.status_code == 401:  # Unauthorized
                messages.error(request, 'Authentication error. Please log in again.')
                # Clear Flask token as it might be invalid
                request.session['flask_token'] = None
                request.session.modified = True
                return redirect('login')
            elif response.status_code == 403:  # Forbidden
                messages.error(request, 'You do not have permission to delete this recipe.')
            elif response.status_code == 404:  # Not Found
                messages.error(request, 'Recipe not found in API. Local copy will still be deleted.')
            else:
                messages.error(request, f'API Error: {response.status_code} - {response.text}')
                
        except requests.RequestException as e:
            # Handle API connection error - fallback to Django model
            print(f"Flask API connection error: {str(e)}. Falling back to Django model.")
            messages.warning(request, 'API connection failed. Recipe will be deleted from local database only.')
            
        # Always delete from Django database to keep in sync
        recipe.delete()
        messages.success(request, 'Recipe deleted from local database.')
        
    except Exception as e:
        messages.error(request, f'Error deleting recipe: {str(e)}')
    
    return redirect('alladdedrecipespage')




def user_recipes(request, username):
    user = get_object_or_404(User, username=username)
    recipes = Recipe.objects.filter(author=user).order_by('-created_at')
    return render(request, 'user_recipes.html', {'recipes': recipes, 'profile_user': user})




def recipe_detail(request, recipe_id):
    # Get base recipe (could be original or translation)
    base_recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Determine original recipe
    original_recipe = base_recipe.original_recipe if base_recipe.is_translation else base_recipe
    
    # Language detection logic
    user_language = 'en'
    if request.user.is_authenticated:
        try:
            user_pref = UserLanguagePreference.objects.get(user=request.user)
            user_language = user_pref.language
        except UserLanguagePreference.DoesNotExist:
            pass
    elif 'language' in request.session:
        user_language = request.session['language']
    else:
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            user_language = accept_language.split(',')[0].split('-')[0]

    # Get appropriate recipe version
    display_recipe = original_recipe
    is_translated = False
    if user_language != original_recipe.language:
        translated_recipe = original_recipe.get_or_create_translation(user_language)
        if translated_recipe:
            display_recipe = translated_recipe
            is_translated = True

    # Existing functionality
    emoji_counts = {}
    for emoji_code, _ in EmojiReaction.EMOJI_CHOICES:
        emoji_counts[emoji_code] = EmojiReaction.objects.filter(
            recipe=display_recipe, emoji=emoji_code
        ).count()

    user_emojis = {}
    if request.user.is_authenticated:
        user_reactions = EmojiReaction.objects.filter(
            user=request.user, recipe=display_recipe
        )
        user_emojis = {reaction.emoji: True for reaction in user_reactions}

    comments = display_recipe.comments.all().order_by('-created_at')
    comment_form = CommentForm()
    
    user_liked = Like.objects.filter(
        user=request.user, recipe=display_recipe
    ).exists() if request.user.is_authenticated else False

    # Translation context
    all_language_codes = ['en', 'es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ar', 'ru', 'hi', 'pa', 'gu', 'ta', 'te', 'bn']
    available_languages = [{'code': code, 'name': get_language_name(code)} for code in all_language_codes]

    context = {
        # Original functionality
        'recipe': display_recipe,
        'comments': comments,
        'comment_form': comment_form,
        'user_liked': user_liked,
        'emoji_choices': EmojiReaction.EMOJI_CHOICES,
        'emoji_counts': emoji_counts,
        'user_emojis': user_emojis,
        
        # Translation functionality
        'original_recipe': original_recipe,
        'is_translated': is_translated,
        'original_language': get_language_name(original_recipe.language),
        'current_language': get_language_name(user_language),
        'available_languages': available_languages,
    }

    # Approval warning
    if display_recipe.status != 'approved' and not request.user.is_superuser and request.user != display_recipe.author:
        messages.warning(
            request,
            "This recipe is not yet approved and is only visible to you as the author and administrators."
        )

    return render(request, 'recipe_detail.html', context)



@login_required
@require_POST
def like_recipe(request):
    recipe_id = request.POST.get('recipe_id')
    recipe = get_object_or_404(Recipe, id=recipe_id)
    like, created = Like.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        like.delete()
        is_liked = False
    else:
        is_liked = True
    return JsonResponse({
        'is_liked': is_liked,
        'total_likes': recipe.total_likes()
    })

@login_required
@require_POST
def add_comment(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    parent_id = request.POST.get('parent_id')
    parent = None
    if parent_id:
        try:
            parent = Comment.objects.get(id=parent_id)
        except Comment.DoesNotExist:
            parent = None

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.recipe = recipe
        comment.parent = parent
        comment.save()
        return redirect('recipe_detail', recipe_id=recipe_id)
    return redirect('recipe_detail', recipe_id=recipe_id)

# Update homepage_view in FlavorverseApp/views.py to only show approved recipes
def homepage_view(request):
    # Import Recipe model here to avoid circular imports
    from RecipesApp.models import Recipe
    
    # Get the latest approved user-added recipes (limit to 5)
    user_recipes = Recipe.objects.filter(status='approved').order_by('-created_at')[:5]
    
    context = {
        'user_recipes': user_recipes
    }
    return render(request, "home.html", context)

# Add a new view for users to see their pending recipes
@login_required
def my_pending_recipes_view(request):
    # Get recipes for the current user with different statuses
    pending_recipes = Recipe.objects.filter(user=request.user, status='pending').order_by('-created_at')
    approved_recipes = Recipe.objects.filter(user=request.user, status='approved').order_by('-updated_at')
    rejected_recipes = Recipe.objects.filter(user=request.user, status='rejected').order_by('-updated_at')
    
    context = {
        'pending_recipes': pending_recipes,
        'approved_recipes': approved_recipes,
        'rejected_recipes': rejected_recipes
    }
    
    return render(request, 'my_pending_recipes.html', context)

# Add admin recipe approval view
@login_required
def admin_recipe_approval_view(request):
    # Check if user is admin/superuser
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('homepage')
    
    pending_recipes = Recipe.objects.filter(status='pending').order_by('-created_at')
    
    context = {
        'pending_recipes': pending_recipes
    }
    
    return render(request, 'admin_recipe_approval.html', context)

# Add approve/reject recipe view
@login_required
def approve_reject_recipe(request, recipe_id):
    # Check if user is admin/superuser
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': "You don't have permission to perform this action."}, status=403)
    
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    if request.method == 'POST':
        # Get action from URL parameter or POST data
        action = request.GET.get('action') or request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        try:
            if action == 'approve':
                recipe.status = 'approved'
                recipe.admin_notes = admin_notes
                recipe.updated_at = timezone.now()
                recipe.save()
                return JsonResponse({
                    'status': 'success',
                    'message': f'Recipe "{recipe.title}" has been approved.'
                })
            elif action == 'reject':
                recipe.status = 'rejected'
                recipe.admin_notes = admin_notes
                recipe.updated_at = timezone.now()
                recipe.save()
                return JsonResponse({
                    'status': 'success',
                    'message': f'Recipe "{recipe.title}" has been rejected.'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': "Invalid action specified."
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    # If it's a GET request, show the detailed approval page
    return render(request, 'approve_reject_recipe.html', {'recipe': recipe})

@require_POST
@login_required
def toggle_emoji_reaction(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    emoji = request.POST.get('emoji')
    
    if not emoji or emoji not in dict(EmojiReaction.EMOJI_CHOICES):
        return JsonResponse({'error': 'Invalid emoji'}, status=400)
    
    try:
        reaction = EmojiReaction.objects.get(user=request.user, recipe=recipe, emoji=emoji)
        reaction.delete()
        action = 'removed'
    except EmojiReaction.DoesNotExist:
        EmojiReaction.objects.create(user=request.user, recipe=recipe, emoji=emoji)
        action = 'added'
    
    # Get updated reaction counts
    reaction_counts = {}
    for emoji_code, _ in EmojiReaction.EMOJI_CHOICES:
        reaction_counts[emoji_code] = EmojiReaction.objects.filter(recipe=recipe, emoji=emoji_code).count()
    
    return JsonResponse({
        'action': action,
        'reaction_counts': reaction_counts
    })

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user == request.user:
        recipe_id = comment.recipe.id
        comment.delete()
        messages.success(request, "Comment deleted.")
        return redirect('recipe_detail', recipe_id=recipe_id)
    else:
        messages.error(request, "You can only delete your own comments.")
        return redirect('recipe_detail', recipe_id=comment.recipe.id)
    



@require_POST
def change_language(request):
    """
    Change language preference for recipes
    """
    language = request.POST.get('language', 'en')
    
    # If user is logged in, save preference to their profile
    if request.user.is_authenticated:
        preference, created = UserLanguagePreference.objects.get_or_create(
            user=request.user
        )
        preference.language = language
        preference.save()
    
    # Also save to session for non-logged in users
    request.session['language'] = language
    
    # Redirect back to previous page
    redirect_url = request.POST.get('next', 'home')
    return redirect(redirect_url)

@login_required
def translate_recipe_ajax(request, recipe_id):
    """
    API endpoint to translate recipe on-demand
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    language = request.GET.get('language', 'en')
    
    try:
        # Get or create translation
        if recipe.is_translation:
            original = recipe.original_recipe
            if not original:
                return JsonResponse({'error': 'Cannot find original recipe'}, status=400)
            translated = original.get_or_create_translation(language)
        else:
            translated = recipe.get_or_create_translation(language)
            
        if translated:
            return JsonResponse({
                'success': True,
                'recipe_id': translated.id,
                'title': translated.title,
                'description': translated.description,
                'ingredients': translated.ingredients,
                'instructions': translated.instructions,
                'language': translated.language,
                'language_name': get_language_name(translated.language)
            })
        else:
            return JsonResponse({'error': 'Translation failed'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def add_recipe_direct(request):
    """Alternative recipe submission that doesn't rely on the Flask API"""
    if request.method == 'POST':
        try:
            # Validate required fields
            title = request.POST.get('title')
            ingredients = request.POST.get('ingredients')
            instructions = request.POST.get('instructions')
            category = request.POST.get('category')
            
            if not all([title, ingredients, instructions, category]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'addyourrecipe.html')
            
            # Validate ingredients format - make sure there are enough segments (at least 3 ingredients)
            ingredients_lines = [line.strip() for line in ingredients.splitlines() if line.strip()]
            if len(ingredients_lines) < 3:
                messages.error(request, 'Please add at least 3 ingredients, each on a separate line.')
                return render(request, 'addyourrecipe.html')
            
            # Validate instructions format - make sure there are enough segments (at least 2 steps)
            instructions_lines = [line.strip() for line in instructions.splitlines() if line.strip()]
            if len(instructions_lines) < 2:
                messages.error(request, 'Please add at least 2 instruction steps, each on a separate line.')
                return render(request, 'addyourrecipe.html')
            
            # Format ingredients and instructions properly
            ingredients = "\n".join(ingredients_lines)
            instructions = "\n".join(instructions_lines)
            
            description = request.POST.get('description', '')
            cooking_time = request.POST.get('cooking_time')
            if cooking_time and cooking_time.isdigit():
                cooking_time = int(cooking_time)
            else:
                cooking_time = None
                
            # Create recipe directly in Django model
            recipe = Recipe(
                user=request.user,
                author=request.user,
                title=title,
                description=description,
                ingredients=ingredients,
                instructions=instructions,
                cooking_time=cooking_time,
                category=category,
                status='pending'
            )
            
            # Add image if provided
            if 'image' in request.FILES:
                recipe.image = request.FILES['image']
            
            recipe.save()
            messages.success(request, 'Recipe submitted successfully! It is now pending approval by an administrator.')
            return redirect('my_pending_recipes')
                
        except Exception as e:
            messages.error(request, f'Error adding recipe: {str(e)}')
            return render(request, 'addyourrecipe.html')

    return render(request, 'addyourrecipe.html')