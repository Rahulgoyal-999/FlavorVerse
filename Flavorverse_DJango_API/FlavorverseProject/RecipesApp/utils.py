# Create a new file called utils.py in your app directory

import uuid
import requests
import json
from django.conf import settings

def translate_text(text, to_language):
    """
    Translate text using Azure Translator API
    """
    if not text:
        return ""
        
    # Get settings
    key = settings.AZURE_TRANSLATOR_KEY
    endpoint = settings.AZURE_TRANSLATOR_ENDPOINT
    location = settings.AZURE_TRANSLATOR_LOCATION
    
    # Set up the API request
    path = '/translate'
    constructed_url = endpoint + path
    
    # Set up parameters
    params = {
        'api-version': '3.0',
        'to': to_language
    }
    
    # Set up headers
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    
    # Create request body
    body = [{
        'text': text
    }]
    
    # Make request
    try:
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse response
        result = response.json()
        
        # Get translated text
        if result and len(result) > 0:
            translations = result[0].get('translations', [])
            if translations and len(translations) > 0:
                return translations[0].get('text', '')
                
        return ""
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text  # Return original text on error

def translate_recipe(recipe, to_language):
    """
    Translate a recipe to the specified language
    Returns a dictionary with translated fields
    """
    # Don't translate if already in target language
    if recipe.language == to_language:
        return None
        
    # Prepare result dictionary
    result = {}
    
    # Translate title
    result['title'] = translate_text(recipe.title, to_language)
    
    # Translate description
    result['description'] = translate_text(recipe.description, to_language)
    
    # Translate ingredients
    # For ingredients, we'll translate the whole block, as line-by-line would be expensive
    result['ingredients'] = translate_text(recipe.ingredients, to_language)
    
    # Translate instructions
    result['instructions'] = translate_text(recipe.instructions, to_language)
    
    return result

def get_language_name(language_code):
    """Return the full name of a language from its code"""
    languages = {
        'en': 'English',
        'es': 'Spanish', 
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ar': 'Arabic',
        'ru': 'Russian',
        'hi': 'Hindi',
        'pa': 'Punjabi',
        'gu': 'Gujarati',
        'ta': 'Tamil',
        'te': 'Telugu',
        'bn': 'Bengali',
        # Add more as needed
    }
    
    return languages.get(language_code, language_code)