from django import forms
from .models import Recipe, Comment

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'description', 'ingredients', 'instructions', 'cooking_time', 'image']
        widgets = {
            'ingredients': forms.Textarea(attrs={'placeholder': 'Enter ingredients, one per line'}),
            'instructions': forms.Textarea(attrs={'placeholder': 'Enter step-by-step instructions'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'placeholder': 'Share your thoughts on this recipe...', 'rows': 3}),
        }
