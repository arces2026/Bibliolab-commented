from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import UserSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def csrf(request):
    token = get_token(request)
    return Response({"csrftoken": token})


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    user = authenticate(
        request,
        username=request.data.get("username"),
        password=request.data.get('password'),
    )
    if user is None:
        return Response({'detail': 'Invalid credentials'}, status=401)
    login(request, user)
    return Response(UserSerializer(user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response(status=204)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)
    