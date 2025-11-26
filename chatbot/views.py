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

RISK_KEYWORDS = {
    'stressed': (-0.8, 1.0),
    'anxious': (-0.8, 1.0),
    'depressed': (-1.0, 1.0),   'suicidal': (-1.0, 1.0),
        'kill': (-1.0, 1.0),        'die': (-1.0, 1.0),
        'pain': (-0.8, 1.0),        'lonely': (-0.7, 1.0),
        'overwhelmed': (-0.5, 1.0), 'sad': (-0.7, 1.0),
        'angry': (-0.5, 1.0),       'horrible': (-0.9, 1.0),
        'terrible': (-0.9, 1.0),    'hopeless': (-1.0, 1.0),
        'happy': (0.8, 1.0),        'excited': (0.8, 1.0),
        'calm': (0.5, 1.0),         'better': (0.5, 1.0),
        'good': (0.6, 1.0),         'great': (0.8, 1.0),
        "kill myself": (-1.0, 1.0), "empty": (-0.7, 1.0), "worthless": (-1.0, 1.0),
        "marne ka mann": (-1.0, 1.0), "marna": (-1.0, 1.0),
        "jeene ka mann nahi": (-1.0, 1.0), "zindagi se thak": (-0.9, 1.0),
        "aatmahatya": (-1.0, 1.0), "dukhi": (-0.6, 1.0), "akela": (-0.7, 1.0),
        "marva nu man": (-1.0, 1.0), "jeevti nathi": (-1.0, 1.0),
        "dukhi chu": (-0.6, 1.0), "bhay lage chhe": (-0.6, 1.0),
    "marva nu man": (-1.0, 1.0), 
}

def AIresponse(user_msg, recent_msgs):
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
    
    for msg in reversed(recent_msgs):
        payload["contents"].append({"role": "user", "parts": [{"text": msg.message}]})
        payload["contents"].append({"role": "model", "parts": [{"text": msg.response}]})
    
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

def compute_scores(messages_list):
    total_polarity = 0.0
    count = 0

    for text in messages_list:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        text_lower = text.lower()
        for word, (score, subj) in RISK_KEYWORDS.items():
            if word in text_lower:
                polarity = score 
                break 
        
        total_polarity += polarity
        count += 1

    if count > 0:
        avg_polarity = total_polarity / count
    else:
        avg_polarity = 0.0

    mood = int((avg_polarity + 1) * 50) 
    stress = 100 - mood
    negative = 100 if avg_polarity < 0 else 0
    
    return mood, stress, negative

def analyze_user_data(user):
    texts = []
    texts += list(ChatMessage.objects.filter(user=user).order_by('-created_at')[:20].values_list("message", flat=True))
    texts += list(GroupMessage.objects.filter(sender=user).order_by('-timestamp')[:20].values_list("content", flat=True))
    texts += list(DirectMessage.objects.filter(sender=user).order_by('-timestamp')[:20].values_list("content", flat=True))

    texts = [t for t in texts if t.strip()]
    
    if len(texts) < 5:
        return None
        
    return texts 

def calculate_risk(stress, negative):
    if stress > 80 or negative > 70: return "High"
    elif stress > 50 or negative > 40: return "Medium"
    return "Low"



@login_required
def chat_page(request):
    from group.views import sidebar_context
    context = sidebar_context(request)
    return render(request, "chatbot/chat.html", context)

@login_required
def analysis_page(request):
    from group.views import sidebar_context
    context = sidebar_context(request)
    return render(request, "chatbot/analysis.html", context)


class ChatAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_msgs = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:50]
        user_msgs = list(user_msgs)[::-1]
        serializer = MessageSerializer(user_msgs, many=True)
        return Response(serializer.data)

    def post(self, request):
        usr_msg = request.data.get('user_message')
        if not usr_msg:
            return Response({"error": "Empty message"}, status=400)

        blob = TextBlob(usr_msg)

        
        polarity = 0.0
        
        lower_msg = usr_msg.lower()
        custom_hit = False
        
        for word, (score, subj) in RISK_KEYWORDS.items():
            if word in lower_msg:
                polarity = score 
                custom_hit = True
                break 
        
        if not custom_hit:
            polarity = blob.sentiment.polarity

 
        print(f"User Message: {usr_msg} | Score: {polarity}") 

        emergency_trigger = False
        emergency_contact = None
        
        if polarity < -0.5: 
            emergency_trigger = True            
            try:
                profile = request.user.profile
                if profile.emergency_name and profile.emergency_phone:
                    emergency_contact = {
                        "name": profile.emergency_name,
                        "phone": profile.emergency_phone
                    }
            except Exception as e:
                print(f"Profile Error: {e}")

        
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
        last_report = AnalysisReport.objects.filter(user=request.user).order_by('-timestamp').first()
        create_new = True
        if last_report:
            if (timezone.now() - last_report.timestamp) < timedelta(seconds=45):
                create_new = False

        if create_new:
            messages_list = analyze_user_data(request.user) 
            
            if messages_list:
                mood, stress, negative = compute_scores(messages_list)
                
                risk = calculate_risk(stress, negative)
                
                
                AnalysisReport.objects.create(
                    user=request.user,
                    mood_score=mood,
                    stress_level=stress,
                    negative_percentage=negative,
                    risk_level=risk 
                )
        
        reports_qs = AnalysisReport.objects.filter(user=request.user).order_by('-timestamp')[:20]
        
        
        reports_list = list(reports_qs)[::-1] 
        
        serializer = AnalysisReportSerializer(reports_list, many=True)
        return Response(serializer.data)

