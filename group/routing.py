from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/direct/<slug:username>/", consumers.DirectChatConsumer.as_asgi()),
    path("ws/groups/<slug:slug>/", consumers.GroupChatConsumer.as_asgi()),
    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
]
