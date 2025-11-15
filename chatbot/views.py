import json
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.response import Response 
from rest_framework.views import APIView
from .models import ChatMessage
from .serializers import MessageSerializer, LoginSerializer, RegisterSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate, login as django_login
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from decouple import config
import requests
from django.conf import settings

def AIresponse(user_msg, recent_msgs):
    short_prompt = f"Act as a Mental Health Chatbot. Give a concise reply (3 to 4 lines) to the user: '{user_msg}'"

    payload = {
        "contents": []
    }

    for msg in reversed(recent_msgs):
        payload["contents"].append({"role": "user", "parts": [{"text": msg.message}]})
        payload["contents"].append({"role": "model", "parts": [{"text": msg.response}]})

    payload["contents"].append({"role": "user", "parts": [{"text": short_prompt}]})

    print("Payload:\n", json.dumps(payload, indent=2))

    headers = {
        "X-goog-api-key": settings.API_KEY,
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(settings.API_URL, headers=headers, json=payload)
        print(response.text)
        response.raise_for_status()  
        data = response.json()

        try:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
            print(reply)
        except (KeyError, IndexError):
            reply = "Sorry, could not parse AI response."

        return reply

    except requests.exceptions.RequestException as e:
        return f"API request error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_msgs = ChatMessage.objects.filter(user=request.user).order_by('-created_at')

        user_msgs = list(user_msgs)[::-1]

        # ✅ Serialize and return
        serializer = MessageSerializer(user_msgs, many=True)
        return Response(serializer.data)
    # 

    def post(self, request):
        usr_msg = request.data.get('user_message')
        recent_msgs = ChatMessage.objects.filter(user=request.user).order_by('-created_at')[:3]
        recent_msgs = list(recent_msgs)[::-1]
        ai_reply = AIresponse(usr_msg, recent_msgs)
        invalid_responses = [
            "API request error",
            "Error:",
            "Sorry, could not parse AI response."
        ]
        print(ai_reply)
        if any(ai_reply.startswith(bad) for bad in invalid_responses):

            return Response(
                {"error": "AI could not generate a valid response."},
                status=500
            )
        data = {
            'user': request.user.id,  
            'message': usr_msg,
            'response': ai_reply
        }
        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)  
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'status': True, 'message': 'User created successfully'},
            status=status.HTTP_201_CREATED
        )
    return Response(
        {'status': False, 'message': serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def validate_token(request):
    return Response({"status": True, "message": "Token is valid"})


from rest_framework import status

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"status": False, "message": "Username and password required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)
    if user:
        django_login(request, user)
        refresh = RefreshToken.for_user(user)
        return Response({
            "status": True,
            "message": "User logged in successfully",
            "token": {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        })
    return Response(
        {"status": False, "message": "Invalid credentials"},
        status=status.HTTP_401_UNAUTHORIZED
    )
