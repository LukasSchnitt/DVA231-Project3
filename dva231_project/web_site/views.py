from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
# from .models import User, BookmarkedCocktail
from .serializers import UserSerializer, BookmarkSerializer, ReviewSerializer
import hashlib
# -----------------------------------------------------
import requests
import json
from .models import *

# ---------------------------------------------------

# Create your views here.
'''
    just for testing purposes, needs to be changed in future
'''


def home(request):
    if 'is_logged_in' in request.session and 'is_moderator' in request.session and \
            request.session['is_logged_in'] and request.session['is_moderator']:
        return HttpResponse("Hello Moderator")
    elif 'is_logged_in' in request.session and request.session['is_logged_in']:
        return HttpResponse("Hello Logged in")
    return HttpResponse("Hello World")


'''
    Allowed Request Methods:
        - GET : used to retrieve all reviews of a cocktail
            @param cocktail_id : integer unique id of the cocktail
            @param is_personal_cocktail : boolean
                                          True if cocktail comes from the DataBase
                                          False if cocktail comes from the Cocktail DB REST API
            @returns HTTP STATUS 404 if there are no reviews for the cocktail
            @returns a json containing all the reviews for that cocktail
                        every element of the json contains 
                            'id' : integer unique identifier of the review
                            'user_id' : integer unique identifier of the user
                            'rating' : double
                            'comment' : string (maximum 500 characters)
    Allowed Request Methods if Logged in:
        - POST : used to add a new review
            @param cocktail_id : integer unique identifier of the cocktail
            @param is_personal_cocktail : boolean
                                          True if cocktail comes from the DataBase
                                          False if cocktail comes from the Cocktail DB REST API
            @param rating : double value from 1 to 5
            @param comment : string (maximum 500 characters)
            @returns HTTP STATUS 201 if review has been added correctly
            @returns HTTP STATUS 400 if data are not valid
        - PUT : used to edit an existing review
            @param id : integer unique identifier of the comment
            depending on what have to be changed one or both of:
                @param rating : double from 1 to 5
                @param comment : string (maximum 500 characters)
            @returns HTTP STATUS 200 if the review has been changed correctly
            @returns HTTP STATUS 400 if data are not changed
            @returns HTTP STATUS 404 if data are not valid
        - DELETE : use to delete an existing review
            @param id : integer unique identifier of the review
            @returns HTTP STATUS 200 if the review has been deleted successfully
            @returns HTTP STATUS 404 if the data are not valid
    If try to POST, PUT or DELETE when not logged in:
        @returns HTTP STATUS 401
'''


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def review(request):
    if request.method == 'GET':
        try:
            cocktail_reviews = Review.objects.filter(cocktail_id=request.GET['cocktail_id'],
                                                    is_personal_cocktail=request.GET['is_personal_cocktail'])\
                .values('id', 'user_id', 'rating', 'comment')
            return Response(data=cocktail_reviews)
        except Review.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    if not ('is_logged_in' in request.session and 'id' in request.session and request.session['is_logged_in']):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'POST':
        data_for_serializer = {
            'user_id': request.session['id'],
            'cocktail_id': request.data['cocktail_id'],
            'is_personal_cocktail': request.data['is_personal_cocktail'],
            'rating': request.data['rating'],
            'comment': request.data['comment']
        }
        serializer = ReviewSerializer(data=data_for_serializer)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PUT':
        try:
            user_review = Review.objects.get(id=request.data['id'], user_id=request.session['id'])
            changed = False
            if 'rating' in request.data:
                user_review.rating = request.data['rating']
                changed = True
            if 'comment' in request.data:
                user_review.comment = request.data['comment']
                changed = True
            if changed:
                user_review.save()
                return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Review.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'DELETE':
        try:
            user_review = Review.objects.get(id=request.data['id'], user_id=request.session['id'])
            user_review.delete()
            return Response(status=status.HTTP_200_OK)
        except Review.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


'''
    @param cocktail_id : integer cocktail id form the REST API
    @returns             dictionary containing 'id'=@param id, 'is_personal_cocktail'=False, 'image', 'name', 'average'
'''


def get_cocktail_from_api_by_id(cocktail_id):
    out = {
        'id': cocktail_id,
        'is_personal_cocktail': False
    }
    return out


'''
    @param cocktail_id : integer cocktail id form the DataBase
    @returns             dictionary containing 'id'=@param id, 'is_personal_cocktail'=True, 'image', 'name', 'average'
'''


def get_cocktail_from_db_by_id(cocktail_id):
    out = {
        'id': cocktail_id,
        'is_personal_cocktail': True
    }
    return out


'''
    user must be logged to use this api, otherwise
        @returns HTTP STATUS 401
    Allowed Request Methods:
        - GET : used to get the list of bookmarked cocktail that a user have 
            @returns HTTP STATUS 404 if user has no bookmarked cocktails
            @returns dictionary rendered as json containing all the cocktail bookmarked by a user
                        every element in the dictionary contains  
                        <int>:'id', <boolean>:'is_personal_cocktail', <url>:'image', <string>:'name', <double>:'average'
        - POST : used to add a new cocktail in the user bookmarks
            @param cocktail_id : integer unique identifier of a cocktail
            @param is_personal_cocktail : boolean 
                                                True if cocktail comes from the database
                                                False if cocktail comes from the REST API
            @returns HTTP STATUS 200    if cocktail has been added
            @returns HTTP STATUS 400    if @params are not valid
        - DELETE : used to remove a cocktail from the user bookmarks
            @param cocktail_id : integer unique identifier of a cocktail
            @param is_personal_cocktail : boolean 
                                                True if cocktail comes from the database
                                                False if cocktail comes from the REST API
            @returns HTTP STATUS 200    if cocktail has been removed
            @returns HTTP STATUS 401    if @params are not valid
'''


@api_view(['GET', 'POST', 'DELETE'])
def bookmark(request):
    if not ('is_logged_in' in request.session and 'id' in request.session and request.session['is_logged_in']):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'GET':  # get bookmark
        try:
            user_bookmarks = BookmarkedCocktail.objects.filter(user_id=request.session['id']) \
                .values('cocktail_id', 'is_personal_cocktail')
            response = {}
            index = 0
            for row in user_bookmarks:
                if row['is_personal_cocktail']:
                    response[index] = get_cocktail_from_api_by_id(row['cocktail_id'])
                else:
                    response[index] = get_cocktail_from_db_by_id(row['cocktail_id'])
                index += 1
            return Response(data=response)
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
            return Response(status=status.HTTP_200_OK)
        except BookmarkedCocktail.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


'''
    Allowed Request Methods:
        - GET : used to logout
            @returns HTTP STATUS 200 if user is correctly logged out
            @returns HTTP STATUS 400 if user is not logged in
        - POST : used to login
            @param username : string
            @param password : string (possibly encrypt the password on the client-side before sending it)
            @returns HTTP STATUS 200 : if user is correctly logged in
            @returns HTTP STATUS 403 : if user is banned
            @returns HTTP STATUS 404 : if the credentials are invalid or the user is not registered
        - PUT : used to register
            @param username : string
            @param password : string (possibly encrypt the password on the client-side before sending it)
            @returns HTTP STATUS 201 : if user is correctly registered
            @returns HTTP STATUS 400 : if the credentials are invalid
        - DELETE : used to remove a user
            @param username : string
            @param password : string (possibly encrypt the password on the client-side before sending it)
            @returns HTTP STATUS 200 : if user is correctly deleted
            @returns HTTP STATUS 401 : if the credentials are invalid or the user is not registered
'''


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def user(request):
    if request.method == 'GET':  # logout
        if 'is_logged_in' in request.session and request.session['is_logged_in']:
            del request.session['is_logged_in']
            del request.session['is_moderator']
            del request.session['id']
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'POST':  # login
        try:
            pwd = hashlib.sha256(request.data['password'].encode()).hexdigest()
            user_login = User.objects.get(username=request.data['username'], password=pwd)
            if user_login.is_banned:
                return Response(status=status.HTTP_403_FORBIDDEN)
            request.session['is_logged_in'] = True
            request.session['is_moderator'] = user_login.is_moderator
            request.session['id'] = user_login.id
            return Response(status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
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
            return Response(status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


# ----------------------------------------------------------------------------------
# from now, testing part

# response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/search.php?s=margarita")

# response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=gin")
# object1 = response.json()
# response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=lemon")
# object2 = response.json()


def get_cocktail_by_ingredients(ingredient):
    # Use https://www.thecocktaildb.com/api/json/v1/1/filter.php?i='ingredient' for get possible Cocktails
    # Send Back JSON with list of Cocktails containing (Cocktailname, Picture, Ingredients, Recipe, ID)
    json_template = {"cocktails": []}
    cocktail_template = {"name": "", "picture": "", "id": ""}

    api_url = "https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=" + str(ingredient)

    response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=" + str(ingredient))

    data = response.json()

    for cocktail in data["drinks"]:
        cocktail_template["name"] = cocktail["strDrink"]
        cocktail_template["picture"] = cocktail["strDrinkThumb"]
        cocktail_template["id"] = cocktail["idDrink"]
        json_template["cocktails"].append(cocktail_template.copy())
    return json.dumps(json_template)


def get_database_cocktails(ingredient):
    result1 = IngredientsList.objects.filter(name=ingredient)
    print(result1)


def test(request):
    get_database_cocktails("ingredient1")
    return HttpResponse("done")
