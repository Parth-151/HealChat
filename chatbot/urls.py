from django.urls import path
from . import views

app_name = 'chatbot'  # This enables 'chatbot:analysis_page'

urlpatterns = [
    # Pages (HTML)
    path('chat/', views.chat_page, name='chat_page'),
    path('analysis/', views.analysis_page, name='analysis_page'),

    # APIs (JSON)
    path('api/chat/', views.ChatAPIView.as_view(), name='api_chat'),
    path('api/reports/', views.AnalysisAPIView.as_view(), name='api_reports'),
    
    # Auth (Keep these for the Rest API if needed, otherwise handled by users app)
    # path('register/', views.register),
    # path('login/', views.login),
]
