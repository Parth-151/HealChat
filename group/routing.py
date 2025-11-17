from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/groups/(?P<slug>[-\w]+)/$", consumers.GroupChatConsumer.as_asgi()),
    re_path(r"ws/chat/(?P<username>[-\w]+)/$", consumers.DirectChatConsumer.as_asgi()),
]
