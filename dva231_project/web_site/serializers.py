from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'is_moderator', 'is_banned']

    def create(self, validated_data):
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('username', instance.password)
        instance.is_moderator = validated_data.get('username', instance.is_moderator)
        instance.is_banned = validated_data.get('username', instance.is_banned)
        instance.save()
        return instance

