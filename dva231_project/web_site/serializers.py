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


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookmarkedCocktail
        fields = ['user_id', 'cocktail_id', 'is_personal_cocktail']

    def create(self, validated_data):
        return BookmarkedCocktail.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.user_id = validated_data.get('user_id', instance.user_id)
        instance.cocktail_id = validated_data.get('cocktail_id', instance.cocktail_id)
        instance.is_personal_cocktail = validated_data.get('is_personal_cocktail', instance.is_personal_cocktail)
        instance.save()
        return instance


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['user_id', 'cocktail_id', 'is_personal_cocktail', 'rating', 'comment']

    def create(self, validated_data):
        return Review.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.user_id = validated_data.get('user_id', instance.user_id)
        instance.cocktail_id = validated_data.get('cocktail_id', instance.cocktail_id)
        instance.is_personal_cocktail = validated_data.get('is_personal_cocktail', instance.is_personal_cocktail)
        instance.rating = validated_data.get('rating', instance.rating)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.save()
        return instance
