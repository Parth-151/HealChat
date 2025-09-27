from django.urls import path
from . import views
from .views import ChatMessageView

app_name = 'chatbot'

urlpatterns = [
    path('chat/', ChatMessageView.as_view(), name='chat'),
    path('register/', views.register),
    path('login/', views.login),
    path('validate-token/', views.validate_token),
]