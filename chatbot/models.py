from django.db import models

class ChatMessage(models.Model):
    message = models.CharField(max_length=300)
    response = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.message[0:30]+'...'