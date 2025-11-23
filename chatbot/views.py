# chatbot/views.py
import json
import requests
import textblob
from textblob import TextBlob
from textblob.sentiments import PatternAnalyzer
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from .models import ChatMessage, AnalysisReport
from .serializers import MessageSerializer, AnalysisReportSerializer
from group.models import GroupMessage, DirectMessage
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# --- HELPER: AI Logic ---
def AIresponse(user_msg, recent_msgs):
    # Refined Persona: Warm, Professional, Concise.
    system_instruction = (
        "You are HealChat AI, a compassionate mental health companion. "
        "Your goal is to provide emotional support, validate feelings, and offer gentle coping techniques. "
        "GUIDELINES: "
        "1. Keep responses conversational and short (max 3-4 sentences). "
        "2. Be empathetic and non-judgmental. Never dismiss the user's pain. "
        "3. Do NOT provide medical diagnoses or prescribe medication. "
        "4. If the user expresses self-harm or severe danger, prioritize their safety and suggest professional help immediately."
    )

    payload = { "contents": [] }
    
    # Add context (Last 3 messages)
    for msg in reversed(recent_msgs):
        payload["contents"].append({"role": "user", "parts": [{"text": msg.message}]})
        payload["contents"].append({"role": "model", "parts": [{"text": msg.response}]})
    
    # Add System Prompt + Current Message
    final_prompt = f"{system_instruction}\n\nUser says: {user_msg}"
    payload["contents"].append({"role": "user", "parts": [{"text": final_prompt}]})

    headers = {
        "X-goog-api-key": settings.API_KEY,
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(settings.API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm having trouble connecting right now, but I'm here with you. Please try again in a moment."

# --- HELPER: Analysis Logic ---
def compute_scores(text):
    # Custom Dictionary: Calibrated for Mental Health Context
    # Format: 'word': (polarity, subjectivity)
    # Polarity: -1.0 (Negative) to +1.0 (Positive)
    new_words = {
        'stressed': (-0.6, 1.0),    'anxious': (-0.6, 1.0),
        'depressed': (-1.0, 1.0),   'suicidal': (-1.0, 1.0),
        'kill': (-1.0, 1.0),        'die': (-1.0, 1.0),
        'pain': (-0.8, 1.0),        'lonely': (-0.7, 1.0),
        'overwhelmed': (-0.5, 1.0), 'sad': (-0.7, 1.0),
        'angry': (-0.5, 1.0),       'horrible': (-0.9, 1.0),
        'terrible': (-0.9, 1.0),    'hopeless': (-1.0, 1.0),
        'happy': (0.8, 1.0),        'excited': (0.8, 1.0),
        'calm': (0.5, 1.0),         'better': (0.5, 1.0),
        'good': (0.6, 1.0),         'great': (0.8, 1.0)
    }

    # Override Analysis
    blob = TextBlob(text)
    polarity = 0.0
    custom_hit = False
    
    # Check for keywords manually to ensure accuracy
    text_lower = text.lower()
    for word, (score, subj) in new_words.items():
        if word in text_lower:
            polarity = score
            custom_hit = True
            break # Take the strongest sentiment found
    
    if not custom_hit:
        polarity = blob.sentiment.polarity

    mood = int((polarity + 1) * 50) # Convert -1..1 to 0..100
    stress = 100 - mood
    negative = 100 if polarity < 0 else 0
    return mood, stress, negative

def analyze_user_data(user):
    texts = []
    texts += list(ChatMessage.objects.filter(user=user).values_list("message", flat=True))
    texts += list(GroupMessage.objects.filter(sender=user).values_list("content", flat=True))
    texts += list(DirectMessage.objects.filter(sender=user).values_list("content", flat=True))
    
    full_text = " ".join(texts).strip()
    if len(full_text) < 10: return None
    return full_text

def calculate_risk(stress, negative):
    if stress > 80 or negative > 70: return "High"
    elif stress > 50 or negative > 40: return "Medium"
    return "Low"

# ... (The rest of your API Views remain the same as we fixed earlier) ...

@login_required
def chat_page(request):
    # We need to pass the sidebar context manually since this isn't in the 'group' app
    from group.views import sidebar_context
    context = sidebar_context(request)
    return render(request, "chatbot/chat.html", context)

@login_required
def analysis_page(request):
    # Calculate stats on page load (or you can rely solely on API)
    from group.views import sidebar_context
    context = sidebar_context(request)
    return render(request, "chatbot/analysis.html", context)

# =========================================
# 2. API VIEWS (Handle AJAX)
# =========================================

class ChatAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ... (Keep existing get logic) ...
        user_msgs = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:50]
        user_msgs = list(user_msgs)[::-1]
        serializer = MessageSerializer(user_msgs, many=True)
        return Response(serializer.data)

    def post(self, request):
        usr_msg = request.data.get('user_message')
        if not usr_msg:
            return Response({"error": "Empty message"}, status=400)

        # --- 1. FORCE UPDATE LEXICON (Teach it mental health words) ---
        # Custom Dictionary for Mental Health
        new_words = {
            'stressed': (-0.8, 1.0),
            'anxious': (-0.8, 1.0),
            'depressed': (-1.0, 1.0),
            'suicidal': (-1.0, 1.0),
            'kill': (-1.0, 1.0),
            'die': (-1.0, 1.0),
            'pain': (-0.9, 1.0),
            'lonely': (-0.7, 1.0),
            'overwhelmed': (-0.6, 1.0),
            'sad': (-0.8, 1.0),
            'angry': (-0.5, 1.0),
            'horrible': (-1.0, 1.0),
            'terrible': (-1.0, 1.0)
        }

        # FIX: Create Blob first, then update its analyzer's lexicon specifically
        blob = TextBlob(usr_msg)
        
        # This is the correct way to access the lexicon in TextBlob's PatternAnalyzer
        # It might be stored in _lexicon or sentiments variable depending on version
        # The safest way is to update the sentiments dictionary directly if possible, 
        # BUT for PatternAnalyzer, the dictionary is usually loaded from xml.
        
        # SIMPLER HACK: 
        # Since updating PatternAnalyzer is tricky/broken in some versions, 
        # we will check our keyword list MANUALLY first.
        
        polarity = 0.0
        
        # Check if any of our trigger words appear in the message
        lower_msg = usr_msg.lower()
        custom_hit = False
        
        for word, (score, subj) in new_words.items():
            if word in lower_msg:
                polarity = score # Force the score
                custom_hit = True
                break # Stop after finding the first strong negative word
        
        # If no custom word found, let TextBlob calculate normally
        if not custom_hit:
            polarity = blob.sentiment.polarity

        # Debug Print
        print(f"User Message: {usr_msg} | Score: {polarity}") 

        emergency_trigger = False
        emergency_contact = None
        
        # Check Threshold
        # Inside ChatAPIView.post
        if polarity < -0.5: 
            emergency_trigger = True            
            try:
                profile = request.user.profile
                # Check BOTH fields are not None/Empty
                if profile.emergency_name and profile.emergency_phone:
                    emergency_contact = {
                        "name": profile.emergency_name,
                        "phone": profile.emergency_phone
                    }
            except Exception as e:
                print(f"Profile Error: {e}")

        # --- 2. AI Logic ---
        recent_msgs = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:3]
        recent_msgs = list(recent_msgs)[::-1]
        
        if emergency_trigger:
            usr_msg_prompt = f"[CRITICAL: User seems suicidal or very depressed. Suggest seeking help.] User says: {usr_msg}"
        else:
            usr_msg_prompt = usr_msg

        ai_reply = AIresponse(usr_msg_prompt, recent_msgs)

        msg_instance = ChatMessage.objects.create(
            user=request.user,
            message=usr_msg,
            response=ai_reply,
            emotion="Negative" if polarity < 0 else "Positive"
        )
        
        return Response({
            "message": msg_instance.message,
            "response": msg_instance.response,
            "emergency_trigger": emergency_trigger, 
            "emergency_contact": emergency_contact 
        })
    
class AnalysisAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Check Logic (Prevent Duplicate Reports on Refresh)
        last_report = AnalysisReport.objects.filter(user=request.user).order_by('-timestamp').first()
        create_new = True
        if last_report:
            if (timezone.now() - last_report.timestamp) < timedelta(seconds=10): #minutes=10
                create_new = False

        # 2. Create Report with RISK Logic
        if create_new:
            text = analyze_user_data(request.user)
            if text:
                mood, stress, negative = compute_scores(text)
                
                # --- CALCULATE RISK HERE ---
                risk = calculate_risk(stress, negative)
                
                AnalysisReport.objects.create(
                    user=request.user,
                    mood_score=mood,
                    stress_level=stress,
                    negative_percentage=negative,
                    risk_level=risk # <--- NOW IT IS SAVED
                )
        
        reports_qs = AnalysisReport.objects.filter(user=request.user).order_by('-timestamp')[:20]
        
        # Convert to list and REVERSE it so it reads Oldest -> Newest (Left -> Right)
        reports_list = list(reports_qs)[::-1] 
        
        serializer = AnalysisReportSerializer(reports_list, many=True)
        return Response(serializer.data)

