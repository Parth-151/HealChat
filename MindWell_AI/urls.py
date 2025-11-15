from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/chatbot/', include('chatbot.urls')),
    path('users/', include('users.urls')),
    path('groups/', include('group.urls'),)
]
