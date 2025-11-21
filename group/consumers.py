# group/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import Group, GroupMessage, DirectMessage
from django.utils import timezone

User = get_user_model()

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        self.group_name = f"group_{self.slug}"

        # check membership before accepting
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        # verify membership (sync DB)
        is_member = await database_sync_to_async(self._is_member)()
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    def _is_member(self):
        try:
            g = Group.objects.get(slug=self.slug)
            return g.members.filter(id=self.scope["user"].id).exists()
        except Group.DoesNotExist:
            return False

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        user = self.scope["user"]
        data = json.loads(text_data)
        content = data.get("message", "").strip()
        if not content:
            return

        # save message
        msg = await database_sync_to_async(self._save_message)(user, content)

        # broadcast
        payload = {
            "type": "chat.message",
            "id": msg.id,
            "sender": user.username,
            "message": content,
            "timestamp": msg.timestamp.isoformat()
        }
        await self.channel_layer.group_send(self.group_name, payload)

    def _save_message(self, user, content):
        g = Group.objects.get(slug=self.slug)
        m = GroupMessage.objects.create(group=g, sender=user, content=content)
        return m

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "sender": event["sender"],
            "message": event["message"],
            "timestamp": event["timestamp"],
        }))


class DirectChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.other_username = self.scope["url_route"]["kwargs"]["username"]
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        # other user must exist
        other = await database_sync_to_async(self._get_user)(self.other_username)
        if not other:
            await self.close()
            return

        # group name deterministic for both users
        users = sorted([self.user.username, self.other_username])
        self.room_name = f"direct_{users[0]}_{users[1]}"

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    def _get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    # Inside DirectChatConsumer class...

    async def receive(self, text_data):
        user = self.user
        data = json.loads(text_data)
        content = data.get("message", "").strip()
        if not content:
            return

        receiver = await database_sync_to_async(self._get_user)(self.other_username)
        if not receiver:
            return

        # 1. Save the message (Existing logic)
        msg = await database_sync_to_async(self._save_direct)(user, receiver, content)

        # 2. Send to the Chat Room (Existing logic - for the active chat)
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "direct.message",
                "id": msg.id,
                "sender": user.username,
                "receiver": receiver.username,
                "message": content,
                "timestamp": msg.timestamp.isoformat()
            }
        )

        # 3. NEW: Send Notification to the Receiver's Personal Group
        # This ensures they get it even if they are chatting with someone else
        await self.channel_layer.group_send(
            f"user_{receiver.id}",
            {
                "type": "send_notification",
                "sender": user.username,
                "message": content[:30] + "..." if len(content) > 30 else content,
                "link": f"/groups/chat/{user.username}/" # Link to open the chat
            }
        )

    def _save_direct(self, sender, receiver, content):
        return DirectMessage.objects.create(sender=sender, receiver=receiver, content=content)

    async def direct_message(self, event):
        # If recipient connected, they'll receive. Everyone in group receives (both sides)
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "sender": event["sender"],
            "receiver": event["receiver"],
            "message": event["message"],
            "timestamp": event["timestamp"],
        }))

# Add to the bottom of group/consumers.py

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        # Create a unique group for this specific user
        self.group_name = f"user_{self.user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # This function sends the data to the frontend
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "sender": event["sender"],
            "message": event["message"],
            "link": event["link"]
        }))