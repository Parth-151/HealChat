from django.contrib import admin
from .models import  Profile, Feedback
# Register your models here.
# admin.site.register(FriendRequest)
admin.site.register(Profile)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('message',)