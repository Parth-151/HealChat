from django.db import models
from django.contrib.auth.models import User
import os

def upload_avatar(instance, filename):
    return f"avatars/{instance.user.username}/{filename}"
# users/models.py (only show Profile part)
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to=upload_avatar, blank=True, null=True)
    preset_avatar = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    emergency_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(max_length=20, blank=True, null=True)

    # presence
    last_seen = models.DateTimeField(blank=True, null=True)

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        if self.preset_avatar:
            return f"/static/avatars/defaults/{self.preset_avatar}"
        return "/static/avatars/defaults/default1.png"

    def is_online(self, timeout_seconds=60):
        if not self.last_seen:
            return False
        return (timezone.now() - self.last_seen).total_seconds() < timeout_seconds

    def __str__(self):
        return self.user.username
