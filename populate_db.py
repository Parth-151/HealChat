import os
import django
import random
from django.utils.text import slugify

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MindWell_AI.settings')
django.setup()

from django.contrib.auth.models import User
from group.models import Group, GroupMessage, DirectMessage
from users.models import Profile

# 2. Configuration
PASSWORD = "password123"
DEFAULT_AVATARS = ["default1.png", "default2.png", "default3.png", "default4.png"]

def create_data():
    print("🚀 Starting Database Population...")

    # --- Create Superuser ---
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@example.com", "admin")
        print("✅ Superuser 'admin' created (pass: admin)")

    # --- Create Users ---
    usernames = ["Alice", "Bob", "Charlie", "Diana", "Evan"]
    users = []
    
    for name in usernames:
        user, created = User.objects.get_or_create(username=name, email=f"{name.lower()}@test.com")
        if created:
            user.set_password(PASSWORD)
            user.save()
            
            # Update Profile
            profile = user.profile
            profile.bio = f"Hey there! I am {name}. I love chatting here."
            profile.preset_avatar = random.choice(DEFAULT_AVATARS)
            profile.save()
            print(f"👤 User '{name}' created.")
        users.append(user)

    # --- Create Groups ---
    group_data = [
        ("Anxiety Support", "A safe space to discuss anxiety."),
        ("Tech Talk", "Discussing the latest in AI and Code."),
        ("Music Lovers", "Share your favorite songs."),
        ("Wellness Corner", "Tips for mental health and yoga.")
    ]
    
    groups = []
    admin_user = User.objects.get(username="admin")

    for name, desc in group_data:
        slug = slugify(name)
        group, created = Group.objects.get_or_create(
            slug=slug, 
            defaults={'name': name, 'description': desc, 'created_by': admin_user}
        )
        if created:
            # Add random members
            group.members.add(admin_user)
            for u in random.sample(users, 3):
                group.members.add(u)
            print(f"📢 Group '{name}' created.")
        groups.append(group)

    # --- Create Group Messages ---
    print("💬 Generating Group Chat History...")
    sample_messages = [
        "Hello everyone!", "How is everyone doing today?", 
        "I'm feeling a bit stressed.", "Remember to take deep breaths!",
        "Has anyone tried the new AI feature?", "Yes, it's amazing!",
        "Good morning!", "Any plans for the weekend?"
    ]

    for group in groups:
        # Create 15 random messages per group
        members = list(group.members.all())
        if not members: continue
        
        for _ in range(15):
            sender = random.choice(members)
            GroupMessage.objects.create(
                group=group,
                sender=sender,
                content=random.choice(sample_messages)
            )

    # --- Create Direct Messages ---
    print("📨 Generating Direct Chat History...")
    # Alice talks to Bob
    alice = User.objects.get(username="Alice")
    bob = User.objects.get(username="Bob")
    
    DirectMessage.objects.create(sender=alice, receiver=bob, content="Hey Bob, are you there?")
    DirectMessage.objects.create(sender=bob, receiver=alice, content="Yeah Alice, what's up?")
    DirectMessage.objects.create(sender=alice, receiver=bob, content="Just wanted to check in.")

    print("✨ DONE! Database populated successfully.")

if __name__ == "__main__":
    create_data()