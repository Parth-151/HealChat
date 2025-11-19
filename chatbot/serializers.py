from rest_framework import serializers
from .models import AnalysisReport, ChatMessage
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True)

    # username = serializers.CharField(validators=[UniqueValidator(queryset=User.objects.all())])
    # email = serializers.EmailField(validators=[UniqueValidator(queryset=User.objects.all())])


    class Meta:
        model = User
        fields = ['username', 'email', 'password']
    


    def validate(self, data):
        if data['username']:
            if User.objects.filter(username = data['username']).exists():
                raise serializers.ValidationError('Username is already taken') 
        if data['email']:
            if User.objects.filter(email = data['email']).exists():
                raise serializers.ValidationError('Email is already taken')
        # if len(data['password']) < 6:
        #     raise serializers.ValidationError('Password must be at least 6 characters long')

        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(username=validated_data['username'], email=validated_data['email'], password=validated_data['password'])
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class MessageSerializer(serializers.ModelSerializer):
    # response = serializers.CharField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = '__all__'
    
class AnalysisReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisReport
        fields = "__all__"
        read_only_fields = ("user", "timestamp")
