import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# 1. SETUP DJANGO ENVIRONMENT
# Change 'MindWell_AI' to your project folder name if it is different
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MindWell_AI.settings')
django.setup()

# 2. IMPORT MODELS
from django.contrib.auth import get_user_model
from users.models import Profile
from group.models import Group, GroupMessage
from chatbot.models import ChatMessage, AnalysisReport

User = get_user_model()

def populate():
    print("🚀 Starting Database Population...")

    # --- STEP 1: CREATE USERS ---
    print("Creating Users...")
    
    # User 1: Ram (The Main Demo User)
    Ram, created = User.objects.get_or_create(username='Ram_sharma', email='Ram@example.com')
    if created:
        Ram.set_password('123')
        Ram.save()
        # Update Profile
        p = Profile.objects.get(user=Ram) # Created by signal
        p.emergency_name = "Dad"
        p.emergency_phone = "9876543210"
        p.bio = "Just trying to stay positive through exams."
        p.save()

    # User 2: Priya (The Happy Friend)
    priya, created = User.objects.get_or_create(username='priya_p', email='priya@test.com')
    if created:
        priya.set_password('123')
        priya.save()
        p = Profile.objects.get(user=priya)
        p.bio = "Lover of yoga and meditation. Here to help!"
        p.save()

    # User 3: Rahul (The Stressed Student)
    rahul, created = User.objects.get_or_create(username='rahul_dev', email='rahul@test.com')
    if created:
        rahul.set_password('123')
        rahul.save()
        p = Profile.objects.get(user=rahul)
        p.emergency_name = "Hostel Warden"
        p.emergency_phone = "112"
        p.bio = "Engineering student. Sleep deprived."
        p.save()

    print("✅ Users Created: Ram, Priya, Rahul (Pass: 123)")


    # --- STEP 2: CREATE GROUPS ---
    print("Creating Groups...")
    
    anxiety_group, created = Group.objects.get_or_create(
        slug='anxiety-support',
        defaults={
            'name': 'Anxiety Support',
            'description': 'A safe space to discuss stress, exams, and general anxiety.',
            'created_by': priya
        }
    )
    # Add members
    anxiety_group.members.add(Ram, priya, rahul)
    
    print("✅ Group Created: Anxiety Support")


    # --- STEP 3: CREATE GROUP MESSAGES (With Anonymity) ---
    print("Creating Group Chat History...")

    messages_data = [
        # (Sender, Message, Is_Anonymous, Time_Offset_Minutes)
        (Ram, "Hey guys, is anyone else feeling super anxious about the finals?", False, 60),
        (rahul, "Yes. I haven't slept in 2 days. I feel like I'm going to fail.", True, 55), # Anon
        (priya, "Take a deep breath. We are all in this together. Have you tried the 4-7-8 breathing technique?", False, 50),
        (Ram, "Thanks Priya. It's just hard to focus when there is so much pressure.", True, 45), # Anon
        (rahul, "I just want this week to be over.", True, 40) # Anon
    ]

    for user, text, is_anon, offset in messages_data:
        msg_time = timezone.now() - timedelta(minutes=offset)
        GroupMessage.objects.create(
            group=anxiety_group,
            sender=user,
            content=text,
            is_anonymous=is_anon,
            timestamp=msg_time 
        )
        # Hack to fix auto_now_add overriding our timestamp
        # We have to update it via SQL or raw update after creation
        last_msg = GroupMessage.objects.latest('id')
        last_msg.timestamp = msg_time
        last_msg.save()

    print("✅ Group Messages Inserted")


    # --- STEP 4: CREATE AI CHAT HISTORY (For Ram) ---
    print("Creating AI Chat History...")

    ai_data = [
        ("I feel really overwhelmed with my college project. It feels like too much.", 
         "I hear you, Ram. It’s completely normal to feel overwhelmed by big projects. Have you tried breaking it down into smaller, manageable tasks? Taking it one step at a time can make a huge difference.", 120),
        
        ("That helps. I just feel like I'm running out of time.",
         "Time pressure is tough. Remember to take short breaks to breathe and reset. Your mental health is just as important as the deadline. You've got this.", 118)
    ]

    for user_txt, bot_txt, offset in ai_data:
        msg_time = timezone.now() - timedelta(minutes=offset)
        c = ChatMessage.objects.create(
            user=Ram,
            message=user_txt,
            response=bot_txt,
            emotion="Stressed"
        )
        c.created_at = msg_time
        c.save()

    print("✅ AI Chat History Inserted")


    # --- STEP 5: CREATE ANALYSIS REPORTS (The Graphs) ---
    print("Creating Analysis Reports (The Trend Graph)...")

    # We create a trend: Stressed -> Crisis -> Recovery -> Happy
    report_data = [
        # (Days Ago, Mood, Stress, Risk, Negativity)
        (9, 80, 20, "Low", 10),    # Start good
        (8, 75, 25, "Low", 15),
        (7, 60, 40, "Low", 30),
        (6, 40, 60, "Medium", 50),
        (5, 20, 80, "High", 85),   # CRISIS POINT
        (4, 30, 70, "Medium", 60), # Recovery starts
        (3, 50, 50, "Low", 40),
        (2, 65, 35, "Low", 20),
        (1, 85, 15, "Low", 5),     # Fully Recovered
    ]

    for days, mood, stress, risk, neg in report_data:
        r_time = timezone.now() - timedelta(days=days)
        r = AnalysisReport.objects.create(
            user=Ram,
            mood_score=mood,
            stress_level=stress,
            risk_level=risk,
            negative_percentage=neg,
        )
        r.timestamp = r_time
        r.save()

    print("✅ Analysis Reports Inserted")
    print("🎉 DATABASE POPULATED SUCCESSFULLY!")
    print("👉 Log in as: Ram_sharma / 123")

if __name__ == '__main__':
    populate()