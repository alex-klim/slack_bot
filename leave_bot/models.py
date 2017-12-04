from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .managers import AdminManager


class AdminUser(AbstractBaseUser):
    USERNAME_FIELD = 'email'

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    def get_full_name(self):
        return self.email
    def get_short_name(self):
        return self.email

    objects = AdminManager()


class Message(models.Model):
    author_id = models.CharField(max_length=250)
    author_name = models.CharField(max_length=50)
    text = models.TextField(max_length=250, null=True)
    ts = models.CharField(max_length=250)
    team_id = models.CharField(max_length=250)
    is_answered = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)


class ReplyMessage(models.Model):
    author_id = models.CharField(max_length=250)
    author_name = models.CharField(max_length=50)
    text = models.TextField(max_length=250, null=True)
    origin = models.ForeignKey(Message, related_name='answers')
    ts = models.CharField(max_length=250)
    team_id = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)


class Team(models.Model):
    team_name = models.CharField(max_length=250)
    team_id = models.CharField(max_length=50)
    admin = models.ForeignKey(AdminUser, null=True)
    bot_token = models.CharField(max_length=100)
    bot_id = models.CharField(max_length=25)
    channel = models.CharField(max_length=250)
    moderator_expire = models.PositiveIntegerField(default=60*60*24)


class Token(models.Model):
    token = models.CharField(max_length=150)

