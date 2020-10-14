from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User, BookmarkedCocktail
from .serializers import UserSerializer, BookmarkSerializer
import hashlib


# Create your views here.
def home(request):
    if 'is_logged_in' in request.session and 'is_moderator' in request.session and \
            request.session['is_logged_in'] and request.session['is_moderator']:
        return HttpResponse("Hello Moderator")
    elif 'is_logged_in' in request.session and request.session['is_logged_in']:
        return HttpResponse("Hello Logged in")
    return HttpResponse("Hello World")


@api_view(['GET', 'POST', 'DELETE'])
def bookmark(request):
    if not ('is_logged_in' in request.session and 'id' in request.session and request.session['is_logged_in']):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'GET':  # get bookmark
        try:
            user_bookmarks = BookmarkedCocktail.objects.filter(user_id=request.session['id']).values('cocktail_id', 'is_personal_cocktail')
            for row in user_bookmarks:
                if row['is_personal_cocktail']:
                    pass
                else:
                    pass
            return Response(data=user_bookmarks)
        except BookmarkedCocktail.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'POST':  # add bookmark
        data_for_serializer = {
            'user_id': request.session['id'],
            'cocktail_id': request.data['cocktail_id'],
            'is_personal_cocktail': request.data['is_personal_cocktail']
        }
        serializer = BookmarkSerializer(data=data_for_serializer)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':  # remove bookmark
        try:
            bookmark_to_eliminate = BookmarkedCocktail.objects.get(
                user_id=request.session['id'],
                cocktail_id=request.data['cocktail_id'],
                is_personal_cocktail=request.data['is_personal_cocktail']
            )
            bookmark_to_eliminate.delete()
        except BookmarkedCocktail.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def user(request):
    if request.method == 'POST':  # login
        try:
            pwd = hashlib.sha256(request.data['password'].encode()).hexdigest()
            user_login = User.objects.get(username=request.data['username'], password=pwd)
            if user_login.is_banned:
                return Response(status=status.HTTP_403_FORBIDDEN)
            request.session['is_logged_in'] = True
            request.session['is_moderator'] = user_login.is_moderator
            request.session['id'] = user_login.id
        except User.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_200_OK)
    elif request.method == 'GET':  # logout
        if 'is_logged_in' in request.session and request.session['is_logged_in']:
            del request.session['is_logged_in']
            del request.session['is_moderator']
            del request.session['id']
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PUT':  # register
        request.data['password'] = hashlib.sha256(request.data['password'].encode()).hexdigest()
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':  # remove account
        try:
            pwd = hashlib.sha256(request.data['password'].encode()).hexdigest()
            user_to_eliminate = User.objects.get(username=request.data['username'], password=pwd)
            user_to_eliminate.delete()
        except User.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_200_OK)
