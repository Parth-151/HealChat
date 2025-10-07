from django.db import models
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    emotion = models.CharField(max_length=20, default="Neutral")  
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.message[0:30]+'...'