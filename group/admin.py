from django.contrib import admin
from .models import DirectMessage, Group, GroupMessage
# Register your models here.
admin.site.register(Group)
admin.site.register(GroupMessage)
admin.site.register(DirectMessage)