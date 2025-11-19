from django.db import models
from django.contrib.auth.models import User

def upload_avatar(instance, filename):
    return f"avatars/{instance.user.username}/{filename}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to=upload_avatar, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    friends = models.ManyToManyField("self", blank=True, symmetrical=True)

    emergency_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_requests")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_requests")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user} → {self.to_user}"
