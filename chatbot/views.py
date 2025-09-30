from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.response import Response 
from rest_framework.views import APIView
from .models import ChatMessage
from .serializers import MessageSerializer, LoginSerializer, RegisterSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from decouple import config
import requests
from django.conf import settings

def AIresponse(user_msg):
    short_prompt = f"Act as a Mental Health Chatbot. Give a concise reply (3-4 lines/sentences) to the user: '{user_msg}'"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": short_prompt}]}
        ]
    }
    headers = {
        "X-goog-api-key": settings.API_KEY,
        "Content-Type": "application/json",
    }
    

    try:
        response = requests.post(settings.API_URL, headers=headers, json=payload)
        print(response)
        response.raise_for_status()  # Raise error for HTTP codes >= 400
        data = response.json()

        # Extract reply safely
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
        objs = ChatMessage.objects.all()
        serializer = MessageSerializer(objs, many=True)
        return Response()

    def post(self, request):
        usr_msg = request.data.get('user_message')

        data = {'message':usr_msg, 'response':str(AIresponse(usr_msg))}
        serializer = MessageSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['post'])
@permission_classes([AllowAny]) 
def register(request):
    serializer = RegisterSerializer(data = request.data)

    if not serializer.is_valid():
        return Response({'status':False, 'messsage': serializer.errors})
    
    serializer.save()
    return Response({'status':True, 'messsage': 'User created'})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def validate_token(request):
    return Response({"status": True, "message": "Token is valid"})

@api_view(["post"])
@permission_classes([AllowAny]) 
def login(request):
    serializer = LoginSerializer(data = request.data)

    if not serializer.is_valid():
        return Response({'status':False, 'messsage': serializer.errors})
    
    user = authenticate(username = serializer.validated_data['username'], password = serializer.validated_data['password'])

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': True,
            'message': 'User logged in',
            'token': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    return Response({'status': False, 'message': 'Invalid credentials'})