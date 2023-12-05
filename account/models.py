
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.contrib.auth.hashers import make_password
from os.path import join
import datetime
#create a new user
#create a superuser

class MyAccountManager(UserManager):
    ordering = ('email',)
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        if not email:
            raise ValueError("Email field is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


def get_qr_code_filepath(self, filename):
    return f'frontend/static/images/qr_codes/{self.pk}/qr_code.png'

class Account(AbstractBaseUser):
    username = None
    cafe_name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", default=datetime.datetime.now)
    last_login = models.DateTimeField(verbose_name="last login", default=datetime.datetime.now)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20)
    qr_code = models.ImageField(max_length=255, null=True, blank=True)

    objects = MyAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


    def __str__(self):
        return self.cafe_name

    def get_qr_code_filename(self):
        return str(self.qr_code)[str(self.qr_code).index(f'qr_codes/{self.pk}/')]

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True
