from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView  # <--- IMPORT THIS

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. THE HOME PAGE
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # 2. Your Apps
    path('api/chatbot/', include('chatbot.urls')),
    path('users/', include('users.urls')),
    path('groups/', include('group.urls')), 
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
