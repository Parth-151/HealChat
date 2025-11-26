from django.urls import path
from . import views

app_name = 'chatbot'  

urlpatterns = [
    path('chat/', views.chat_page, name='chat_page'),
    path('analysis/', views.analysis_page, name='analysis_page'),
    path('api/chat/', views.ChatAPIView.as_view(), name='api_chat'),
    path('api/reports/', views.AnalysisAPIView.as_view(), name='api_reports'),
]
