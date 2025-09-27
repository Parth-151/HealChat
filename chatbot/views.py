from django.shortcuts import render
from rest_framework.response import Response 
from rest_framework.views import APIView
from .models import ChatMessage
from .serializers import MessageSerializer, LoginSerializer, RegisterSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

def AIresponse(user_msg):
    if user_msg is None:
        return "Message is required"
    else:
        return "Hey, have a good day"

class ChatMessageView(APIView):

    def get(self, request):
        objs = ChatMessage.objects.all()
        serializer = MessageSerializer(objs, many=True)
        return Response()

    def post(self, request):
        obj = request.data.get('user_message')

        data = {'message':obj, 'response':str(AIresponse(obj))}
        serializer = MessageSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            print(AIresponse(obj))
            return Response(serializer.data)
        return Response(serializer.errors)

@api_view(['post'])
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