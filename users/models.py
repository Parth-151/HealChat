from django.db import models
from django.contrib.auth.models import User
import os

def upload_avatar(instance, filename):
    return f"avatars/{instance.user.username}/{filename}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to=upload_avatar, blank=True, null=True)
    preset_avatar = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    # Emergency contact (optional)
    emergency_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(max_length=20, blank=True, null=True)

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        if self.preset_avatar:
            return f"/static/avatars/defaults/{self.preset_avatar}"
        return "/static/avatars/defaults/default1.png"

    def __str__(self):
        return self.user.username
