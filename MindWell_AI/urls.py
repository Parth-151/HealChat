from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView 
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.home, name='home'),

    path('api/chatbot/', include('chatbot.urls')),
    path('users/', include('users.urls')),
    path('groups/', include('group.urls')), 
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
