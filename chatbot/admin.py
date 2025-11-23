from django.contrib import admin
from .models import ChatMessage, AnalysisReport
# Register your models here.
admin.site.register(ChatMessage)


@admin.register(AnalysisReport)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'risk_level', 'mood_score', 'timestamp')
    list_filter = ('risk_level', 'timestamp') # <--- THIS IS POWERFUL
    search_fields = ('user__username',)