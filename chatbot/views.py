import json
import requests
import textblob
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from .models import ChatMessage, AnalysisReport
from .serializers import MessageSerializer, AnalysisReportSerializer
from group.models import GroupMessage, DirectMessage

# --- HELPER: AI Logic ---
def AIresponse(user_msg, recent_msgs):
    # Your existing logic
    short_prompt = f"Act as a Mental Health Chatbot. Give a concise reply (3 to 4 lines) to the user: '{user_msg}'"
    payload = { "contents": [] }
    for msg in reversed(recent_msgs):
        payload["contents"].append({"role": "user", "parts": [{"text": msg.message}]})
        payload["contents"].append({"role": "model", "parts": [{"text": msg.response}]})
    payload["contents"].append({"role": "user", "parts": [{"text": short_prompt}]})

    headers = {
        "X-goog-api-key": settings.API_KEY,
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(settings.API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        return reply
    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm sorry, I'm having trouble connecting right now. Please try again."

# --- HELPER: Analysis Logic ---
def compute_scores(text):
    blob = textblob.TextBlob(text)
    polarity = blob.sentiment.polarity
    mood = int((polarity + 1) * 50)
    stress = 100 - mood
    negative = 100 if polarity < 0 else 0
    return mood, stress, negative

def analyze_user_data(user):
    texts = []
    texts += list(ChatMessage.objects.filter(user=user).values_list("message", flat=True))
    texts += list(GroupMessage.objects.filter(sender=user).values_list("content", flat=True))
    texts += list(DirectMessage.objects.filter(sender=user).values_list("content", flat=True))
    return " ".join(texts)

# =========================================
# 1. PAGE VIEWS (Render HTML)
# =========================================

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
        user_msgs = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:50]
        user_msgs = list(user_msgs)[::-1]
        serializer = MessageSerializer(user_msgs, many=True)
        return Response(serializer.data)

    def post(self, request):
        usr_msg = request.data.get('user_message')
        if not usr_msg:
            return Response({"error": "Empty message"}, status=400)

        # Get history context for AI
        recent_msgs = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:3]
        recent_msgs = list(recent_msgs)[::-1]
        
        # Call AI
        ai_reply = AIresponse(usr_msg, recent_msgs)

        # Save to DB
        msg_instance = ChatMessage.objects.create(
            user=request.user,
            message=usr_msg,
            response=ai_reply
        )
        
        return Response({
            "message": msg_instance.message,
            "response": msg_instance.response
        })

class AnalysisAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Generate a new report on the fly when requested
        text = analyze_user_data(request.user)
        if not text:
            return Response([]) # No data
            
        mood, stress, negative = compute_scores(text)
        
        # Create report
        AnalysisReport.objects.create(
            user=request.user,
            mood_score=mood,
            stress_level=stress,
            negative_percentage=negative
        )
        
        reports = AnalysisReport.objects.filter(user=request.user).order_by('-timestamp')
        serializer = AnalysisReportSerializer(reports, many=True)
        return Response(serializer.data)