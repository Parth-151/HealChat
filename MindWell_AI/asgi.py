import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import group.routing  

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MindWell_AI.settings')

django_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_app,                      
    "websocket": AuthMiddlewareStack(
        URLRouter(
            group.routing.websocket_urlpatterns
        )
    ),
})
