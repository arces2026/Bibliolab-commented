from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    isStaff = serializers.BooleanField(source="is_staff", read_only=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "isStaff", "password", "password2"]
        # Make password optional for GET requests, required for POST
        extra_kwargs = {
            "password": {"write_only": True, "required": True},
            "password2": {"write_only": True, "required": True},
            "email": {"required": False, "allow_blank": True},
        }

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop("password2")  # Remove password2
        password = validated_data.pop("password")
        user = User.objects.create_user(
            username=validated_data["username"],
            password=password,
            email=validated_data.get("email", ""),
        )
        return user
