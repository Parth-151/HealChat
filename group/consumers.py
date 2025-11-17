import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.shortcuts import get_object_or_404
from .models import DirectMessage, Group, GroupMessage
from django.contrib.auth import get_user_model

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        self.room_group_name = f"group_{self.slug}"

        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message")
        user = self.scope["user"]
        msg_obj = await database_sync_to_async(self.create_message)(user, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": msg_obj.content,
                "username": user.username,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    def create_message(self, user, message):
        # group = Group.objects.get(slug=self.slug)
        group = get_object_or_404(Group, slug=self.slug)
        if not group.members.filter(id=user.id).exists():
            group.members.add(user)
        return GroupMessage.objects.create(group=group, sender=user, content=message)



User = get_user_model()

class DirectChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.other_username = self.scope['url_route']['kwargs']['username']
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return
        if self.other_username == self.user.username:
            await self.close()
            return

        # Create unique room for the two users (alphabetically)
        self.room_group_name = (
            f"dm_{min(self.user.username, self.other_username)}_"
            f"{max(self.user.username, self.other_username)}"
        )

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")

        receiver = await database_sync_to_async(User.objects.get)(username=self.other_username)

        await database_sync_to_async(DirectMessage.objects.create)(
            sender=self.user,
            receiver=receiver,
            content=message
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": self.user.username,
            }
        )

    async def chat_message(self, event):
        await self.send(json.dumps(event))
