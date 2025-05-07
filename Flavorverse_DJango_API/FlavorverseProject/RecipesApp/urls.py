from django.urls import path
from . import views

urlpatterns=[

    path('viewallrecipes/',views.view_all_recipes_view,name='allrecipespage'),
    
    path('desserts/', views.desserts_view,name='desserts'),
    
    path('soups/', views.soups_view,name='soups'),
    
    path('vegetarian/', views.vegetarian_view,name='vegetarian'),
    
    path('non-vegetarian/', views.non_vegetarian_view,name='nonvegetarian'),
    
    path('allrecipes/', views.all_added_recipes_view,name='alladdedrecipespage'),
    
    path('addyourrecipe/',views.add_your_recipe_view,name='addyourrecipepage'),
    
    # Direct recipe submission without API
    path('addrecipe-direct/', views.add_recipe_direct, name='add_recipe_direct'),
    
    path('addedrecipe/', views.added_recipe_view,name='youraddedrecipepage'),

    
    path('lettuce-wrap/', views.lettuce_wrap_view, name='lettuce_wrap'),
    
    path('vegan-fajitas/', views.vegan_fajitas_view, name='vegan_fajitas'),
    
    path('chickpea-curry/', views.chickpea_curry, name='chickpea_curry'),
    path('scallion-roll/', views.scallion_roll, name='scallion_roll'),
    
    path('brussels-sprouts/', views.brussels_sprouts_view, name='brussels_sprouts'),
    
    path('scallion-pancake/', views.scallion_pancake_view, name='scallion_pancake'),
    path('alfredo-sauce/', views.alfredo_sauce_view, name='alfredo_sauce'),
    path('sticky-gochujang-tofu/', views.sticky_gochujang_tofu_view, name='sticky_gochujang_tofu'),
    path('mississippi-pot-roast-cheesesteak/', views.mississippi_pot_roast_cheesesteak_view, name='mississippi_pot_roast_cheesesteak'),
    path('baked-gnocchi/', views.baked_gnocchi_view, name='baked_gnocchi'),
    path('jalapeno-lime-chicken/', views.jalapeno_lime_chicken_view, name='jalapeno_lime_chicken'),
    path('french-silk-pie-bars/', views.french_silk_pie_bars_view, name='french_silk_pie_bars'),
    path('lobster-risotto/', views.lobster_risotto_view, name='lobster_risotto'),
    path('lemon-crumb-bars/', views.lemon_crumb_bars_view, name='lemon_crumb_bars'),

    
    path('edit-recipe/<int:recipe_id>/', views.edit_recipe_view, name='edit_recipe'),
    path('delete-recipe/<int:recipe_id>/', views.delete_recipe_view, name='delete_recipe'),

    # Recipe approval system URLs
    path('my-recipes/', views.my_pending_recipes_view, name='my_pending_recipes'),
    path('viewallrecipes/admin-recipe-approval/', views.admin_recipe_approval_view, name='admin_recipe_approval'),
    path('viewallrecipes/admin-recipe-approval/<int:recipe_id>/', views.approve_reject_recipe, name='approve_reject_recipe'),

    path('recipes/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/like/', views.like_recipe, name='like_recipe'),
    path('recipes/<int:recipe_id>/comment/', views.add_comment, name='add_comment'),
    path('comments/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('user/<str:username>/recipes/', views.user_recipes, name='user_recipes'),
    path('recipes/<int:recipe_id>/toggle-emoji/', views.toggle_emoji_reaction, name='toggle_emoji_reaction'),

    # Change language preference
    path('change-language/', views.change_language, name='change_language'),
    
    # AJAX translation endpoint
    path('translate-recipe/<int:recipe_id>/', views.translate_recipe_ajax, name='translate_recipe_ajax'),


]