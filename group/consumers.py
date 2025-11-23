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
        user = self.scope["user"]
        
        if not user.is_authenticated:
            await self.close()
            return

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
        is_anon = data.get("is_anonymous", False)

        if not content:
            return

        # 1. Save to DB
        msg = await database_sync_to_async(self._save_message)(user, content, is_anon)

        # 2. Determine Display Name
        sender_name = "Anonymous" if is_anon else user.username
        
        # 3. Construct Payload
        payload = {
            "type": "chat.message",
            "id": msg.id,
            "sender": sender_name, 
            "sender_id": user.id,  # CRITICAL: Send the User ID so we can check 'is_me' later
            "message": content,
            "timestamp": msg.timestamp.isoformat(),
            "is_anonymous": is_anon 
        }
        
        # 4. Send to Layer
        await self.channel_layer.group_send(self.group_name, payload)

    def _save_message(self, user, content, is_anon):
        g = Group.objects.get(slug=self.slug)
        return GroupMessage.objects.create(group=g, sender=user, content=content, is_anonymous=is_anon)

    async def chat_message(self, event):
        # 5. The 'is_me' Logic
        # This runs for EVERY user connected to the socket individually.
        # We compare the ID of the message sender with the ID of the current socket user.
        is_me = (event["sender_id"] == self.scope["user"].id)

        await self.send(text_data=json.dumps({
            "id": event["id"],
            "sender": event["sender"], 
            "message": event["message"],
            "timestamp": event["timestamp"],
            "is_anonymous": event["is_anonymous"],
            "is_me": is_me  # Frontend needs this to put bubble on Right or Left
        }))

class DirectChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.other_username = self.scope["url_route"]["kwargs"]["username"]
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        other = await database_sync_to_async(self._get_user)(self.other_username)
        if not other:
            await self.close()
            return

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

    async def receive(self, text_data):
        user = self.user
        data = json.loads(text_data)
        content = data.get("message", "").strip()
        
        # --- FIX: Grab Anonymous Flag ---
        is_anon = data.get("is_anonymous", False) 

        if not content:
            return

        receiver = await database_sync_to_async(self._get_user)(self.other_username)
        if not receiver:
            return

        # 1. Save Message (Note: DirectMessage model might not have is_anonymous field yet. 
        # Ideally Direct messages shouldn't be anonymous, but if you added the button, we handle it)
        # We default is_anon to False for Direct Messages usually, or you need to update DirectMessage model.
        # For now, we assume Direct Chat is ALWAYS real name (safest).
        
        msg = await database_sync_to_async(self._save_direct)(user, receiver, content)

        # 2. Send to Chat
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "direct.message",
                "id": msg.id,
                "sender": user.username, 
                "receiver": receiver.username,
                "message": content,
                "timestamp": msg.timestamp.isoformat(),
                # "is_anonymous": False  <-- Direct chat usually not anon
            }
        )

        # 3. Send Notification
        await self.channel_layer.group_send(
            f"user_{receiver.id}",
            {
                "type": "send_notification",
                "sender": user.username,
                "message": content[:30] + "..." if len(content) > 30 else content,
                "link": f"/groups/chat/{user.username}/"
            }
        )

    def _save_direct(self, sender, receiver, content):
        return DirectMessage.objects.create(sender=sender, receiver=receiver, content=content)

    async def direct_message(self, event):
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "sender": event["sender"],
            "receiver": event["receiver"],
            "message": event["message"],
            "timestamp": event["timestamp"]
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "sender": event["sender"],
            "message": event["message"],
            "link": event["link"]
        }))