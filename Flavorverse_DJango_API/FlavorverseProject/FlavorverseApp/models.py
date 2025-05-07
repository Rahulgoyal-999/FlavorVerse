from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django import forms
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
import requests
import datetime

from django.conf import settings

user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'

# If you need a custom API key model:
class APIKey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255, default='Default API Key')
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.key:
            # Generate a random API key if not provided
            import secrets
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.key[:8]}...)"

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['name'] = user.first_name
        token['email'] = user.email
        # Add any other fields you want in the token

        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class ContactMessage(models.Model):
    """
    Django model that represents contact messages from the Flask API
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # We're not using this field directly, but it helps with DB syncing
    flask_id = models.IntegerField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    @classmethod
    def sync_from_flask(cls):
        """Pull contact messages from Flask API"""
        try:
            print("Starting sync from Flask API...")
            response = requests.get('http://127.0.0.1:5000/api/contact/messages', timeout=5)
            print(f"Flask API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Received data: {data}")
                messages_count = len(data.get('messages', []))
                print(f"Found {messages_count} messages to sync")
                
                synced_count = 0
                for message in data.get('messages', []):
                    # Check if we already have this message by flask_id
                    if not cls.objects.filter(flask_id=message['id']).exists():
                        print(f"Syncing new message: ID={message['id']}, Subject={message['subject']}")
                        cls.objects.create(
                            name=message['name'],
                            email=message['email'],
                            subject=message['subject'],
                            message=message['message'],
                            created_at=datetime.datetime.fromisoformat(message['created_at']),
                            flask_id=message['id']
                        )
                        synced_count += 1
                    else:
                        print(f"Message already exists: ID={message['id']}")
                
                print(f"Sync complete. Added {synced_count} new messages.")
                return True
            else:
                print(f"API request failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error syncing contact messages: {str(e)}")
            import traceback
            traceback.print_exc()
        return False