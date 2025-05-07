from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class RegisterUserManager(BaseUserManager):
    def create_user(self, email, name,phone, address, gender, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field is mandatory')       
        # converting email with lower case
        email= self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            phone=phone,
            address= address,
            gender= gender,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
   
    def create_superuser(self, email, name, phone, address, gender, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)


        if not password:
            raise ValueError("Superusers must have a password.")
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, name, phone, address, gender, password, **extra_fields)


class RegisterUser(AbstractUser):


    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    # redefine the email to be unique
    email = models.EmailField(unique=True)


    # Adding extra field  inside the custom user class
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    avatar = models.ImageField(upload_to='profile_avatars/', null=True, blank=True)
    avatar_url = models.URLField(max_length=500, null=True, blank=True)
    social_provider = models.CharField(max_length=50, null=True, blank=True)
    # removing the username field
    username= None
    objects = RegisterUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone', 'address', 'gender']


    def __str__(self):
        return self.email
