import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Group, GroupMessage

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
                "type": "chat.message",
                "message": msg_obj.content,
                "username": user.username,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    def create_message(self, user, message):
        group = Group.objects.get(slug=self.slug)
        if not group.members.filter(id=user.id).exists():
            group.members.add(user)
        return GroupMessage.objects.create(group=group, sender=user, content=message)
