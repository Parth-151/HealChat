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
    
class AnalysisReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood_score = models.IntegerField()
    stress_level = models.IntegerField()
    negative_percentage = models.FloatField()
    summary = models.TextField(null=True, blank=True)
    risk_level = models.CharField(max_length=20, default="Low")
    timestamp = models.DateTimeField(auto_now_add=True)
