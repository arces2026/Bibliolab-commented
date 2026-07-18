from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    isStaff = serializers.BooleanField(source='is_staff', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'isStaff']