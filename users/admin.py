from django.contrib import admin
from .models import FriendRequest, Profile
# Register your models here.
admin.site.register(FriendRequest)
admin.site.register(Profile)