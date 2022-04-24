from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import Group, User
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer, MyTokenObtainPairSerializer


class RegisterView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        reader_group = Group.objects.get(name='reader')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        reader_group.user_set.add(user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "Пользователь успешно создан",
        })


class ProfileView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        return Response({
            "user": UserSerializer(request.user, context=self.get_serializer_context()).data,
        })


class UsersListView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer