from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import *
import hashlib
from datetime import datetime
import base64
import os
# -----------------------------------------------------
import requests
import json
from .models import *
from django.db.models import Avg

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
    personal_cocktail documentation TO DO
'''


@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def personal_cocktail(request):
    if not ('is_logged_in' in request.session and request.session['is_logged_in']):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'GET':  # get personal cocktail
        try:
            if 'is_moderator' in request.session and request.session['is_moderator']:
                out = user_cocktail(None)
            else:
                out = user_cocktail(request.session['id'])
            return Response(data=out)
        except PersonalCocktail.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'POST':  # create a new cocktail
        now = datetime.now()
        img_url = str(now.year) + str(now.month) + str(now.day) + str(now.hour) \
                  + str(now.minute) + str(now.second) + str(now.microsecond) + '.' + request.data['extension']
        data_for_serializer = {
            'user_id': request.session['id'],
            'name': request.data['name'],
            'description': request.data['description'],
            'picture': img_url,
            'recipe': request.data['recipe']
        }
        serializer = PersonalCocktailSerializer(data=data_for_serializer)
        if serializer.is_valid():
            serializer.save()
            cocktail_id = PersonalCocktail.object.get(user_id=request.session['id'], name=request.data['name'],
                                                      description=request.data['description'], picture=img_url,
                                                      recipe=request.data['recipe']).id
            for ingredient in request.data['ingredients']:
                try:
                    ingredient_id = IngredientsList.objects.get(name=ingredient['name']).id
                except IngredientsList.DoesNotExist:
                    data_for_serializer = {
                        'name': ingredient['name']
                    }
                    serializer = IngredientsListSerializer(data=data_for_serializer)
                    if serializer.is_valid():
                        serializer.save()
                        ingredient_id = IngredientsList.objects.get(name=ingredient['name']).id
                    else:
                        cocktail = PersonalCocktail.get(id=cocktail_id)
                        cocktail.delete()
                        return Response(status=status.HTTP_400_BAD_REQUEST)
                    # add cocktailIngredients
                data_for_serializer = {
                    'cocktail_id': cocktail_id,
                    'ingredient_id': ingredient_id,
                    'centiliters': ingredient['centiliters']
                }
                serializer = CocktailIngredientsSerializer(data=data_for_serializer)
                if serializer.is_valid():
                    serializer.save()
                else:
                    cocktail = PersonalCocktail.get(id=cocktail_id)
                    cocktail.delete()
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            with open("static/img/cocktail/" + request.session['id'] + '/' + img_url, "wb") as f:
                f.write(base64.decodebytes(request.data['img']))
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PATCH':  # edit an existing cocktail
        try:
            cocktail_to_edit = PersonalCocktail.objects.get(id=request.data['cocktail_id'],
                                                            user_id=request.session['id'])
            edited = False
            if 'name' in request.data:
                edited = True
                cocktail_to_edit.name = request.data['name']
            if 'description' in request.data:
                edited = True
                cocktail_to_edit.description = request.data['description']
            if 'recipe' in request.data:
                edited = True
                cocktail_to_edit.recipe = request.data['recipe']
            if 'img' in request.data and 'extension' in request.data:
                edited = True
                os.remove("static/img/cocktail/" + request.session['id'] + '/' + cocktail_to_edit.picture)
                now = datetime.now()
                img_url = str(now.year) + str(now.month) + str(now.day) + str(now.hour) \
                          + str(now.minute) + str(now.second) + str(now.microsecond) + request.data['extension']
                with open("static/img/cocktail/" + request.session['id'] + '/' + img_url, "wb") as f:
                    f.write(base64.decodebytes(request.data['img']))
                cocktail_to_edit.picture = img_url
            if 'ingredients' in request.data:
                for row in CocktailIngredients.objects.filter(cocktail_id=request.data['cocktail_id']):
                    row.delete()
                for ingredient in request.data['ingredients']:
                    try:
                        ingredient_id = IngredientsList.objects.get(name=ingredient['name']).id
                    except IngredientsList.DoesNotExist:
                        data_for_serializer = {
                            'name': ingredient['name']
                        }
                        serializer = IngredientsListSerializer(data=data_for_serializer)
                        if serializer.is_valid():
                            serializer.save()
                            ingredient_id = IngredientsList.objects.get(name=ingredient['name']).id
                        else:
                            cocktail = PersonalCocktail.get(id=request.data['cocktail_id'])
                            cocktail.delete()
                            return Response(status=status.HTTP_400_BAD_REQUEST)
                        # add cocktailIngredients
                    data_for_serializer = {
                        'cocktail_id': request.data['cocktail_id'],
                        'ingredient_id': ingredient_id,
                        'centiliters': ingredient['centiliters']
                    }
                    serializer = CocktailIngredientsSerializer(data=data_for_serializer)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        cocktail = PersonalCocktail.get(id=request.data['cocktail_id'])
                        cocktail.delete()
                        return Response(status=status.HTTP_400_BAD_REQUEST)
            if edited:
                cocktail_to_edit.save()
                return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except PersonalCocktail.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'DELETE':  # remove a cocktail
        try:
            if 'is_moderator' in request.session and request.session['is_moderator'] and 'cocktail_id' in request.data:
                user_cocktail = PersonalCocktail.objects.get(id=request.data['cocktail_id'])
            else:
                user_cocktail = PersonalCocktail.objects.get(id=request.data['id'], user_id=request.session['id'])
            user_cocktail.delete()
            return Response(status=status.HTTP_200_OK)
        except PersonalCocktail.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


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
        - PATCH : used to edit an existing review
            @param id : integer unique identifier of the comment
            depending on what have to be changed one or both of:
                @param rating : double from 1 to 5
                @param comment : string (maximum 500 characters)
            @returns HTTP STATUS 200 if the review has been changed correctly
            @returns HTTP STATUS 400 if data are not changed
            @returns HTTP STATUS 404 if data are not valid
        - DELETE : use to delete an existing review
            if the user is a moderator:
                @param review_id : integer unique identifier of the review 
                                        (if this parameter is not given then a normal DELETE will be done)
            else:
                @param id : integer unique identifier of the review
            @returns HTTP STATUS 200 if the review has been deleted successfully
            @returns HTTP STATUS 404 if the data are not valid
    If try to POST, PUT or DELETE when not logged in:
        @returns HTTP STATUS 401
'''


@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def review(request):
    if request.method == 'GET':
        try:
            cocktail_reviews = Review.objects.filter(cocktail_id=request.GET['cocktail_id'],
                                                     is_personal_cocktail=request.GET['is_personal_cocktail']) \
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
    elif request.method == 'PATCH':
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
            if 'is_moderator' in request.session and request.session['is_moderator'] and 'review_id' in request.data:
                user_review = Review.objects.get(id=request.data['review_id'])
            else:
                user_review = Review.objects.get(id=request.data['id'], user_id=request.session['id'])
            user_review.delete()
            return Response(status=status.HTTP_200_OK)
        except Review.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


'''
    @param cocktail_id : integer cocktail id form the REST API
    @returns             dictionary containing 'id'=@param id, 'is_personal_cocktail'=False, 'image', 'name', 'average'
'''


def get_cocktail_from_api_by_id(id):
    cocktail_template = {"name": "", "picture": "", "id": ""}
    response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i=" + str(id))
    try:
            response = response.json()
    except ValueError:
        return []
    cocktail_data = data["drinks"][0]
    cocktail_template["name"] = cocktail_data["strDrink"]
    cocktail_template["picture"] = cocktail_data["strDrinkThumb"]
    cocktail_template["id"] = id
    if(Review.objects.filter(cocktail_id=id).exists() and Review.objects.filter(cocktail_id=cocktail_template["id"]).values('is_personal_cocktail') == False):
        cocktail_template["rating"] = Review.objects.filter(cocktail_id=id).aggregate(Avg('rating'))['rating']
    return cocktail_template


'''
    @param cocktail_id : integer cocktail id form the DataBase
    @returns             dictionary containing 'id'=@param id, 'is_personal_cocktail'=True, 'image', 'name', 'average'
'''


def get_cocktail_from_db_by_id(id):
    cocktail_template = {"name": "", "picture": "", "id": ""}
    if(PersonalCocktail.objects.filter(cocktail_id=id).exists()):
        cocktail = PersonalCocktail.objects.filter(cocktail_id=id)[0]
        cocktail_template["name"] = cocktail.name
        cocktail_template["picture"] = cocktail.picture
        cocktail_template["id"] = id
        if(Review.objects.filter(cocktail_id=id).exists() and Review.objects.filter(cocktail_id=cocktail_template["id"]).values('is_personal_cocktail') == True):
            cocktail_template["rating"] = Review.objects.filter(cocktail_id=id).aggregate(Avg('rating'))['rating']
        return cocktail_template
    else:
        return {}
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
        - GET : used to retrieve the complete user list (works only for moderators)
            @returns HTTP STATUS 404 if user list is empty (impossible)
            @returns a json containing all the users
                        every element in the json list contains:
                            id : integer unique identifier of the user
                            username : string 
        - HEAD : used to logout
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
            if user is moderator:
                @param id : integer unique identifier of the user 
                                    (if this parameter is missing then a normal delete will be done)
                @returns HTTP STATUS 200 : if user banned status is correctly switched
                                                (if user was banned, now is not banned, 
                                                otherwise the opposite effect is triggered)
                @returns HTTP STATUS 401 : if the data are invalid or the user is not registered
            else:
                @param username : string
                @param password : string (possibly encrypt the password on the client-side before sending it)
                @returns HTTP STATUS 200 : if user is correctly deleted
                @returns HTTP STATUS 401 : if the credentials are invalid or the user is not registered
    If a different method is used:
        @returns HTTP STATUS 409
'''


@api_view(['GET', 'HEAD', 'POST', 'PUT', 'DELETE'])
def user(request):
    if request.method == 'GET' and 'is_moderator' in request.session and request.session['is_moderator']:
        try:
            user_list = User.objects.all().values('id', 'username')
            return Response(data=user_list)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'HEAD':  # logout
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
            if 'is_moderator' in request.session and request.session['is_moderator'] and 'id' in request.data:
                user_to_eliminate = User.objects.get(id=request.data['id'])
                user_to_eliminate.is_banned = not user_to_eliminate.is_banned
                user_to_eliminate.save()
            else:
                pwd = hashlib.sha256(request.data['password'].encode()).hexdigest()
                user_to_eliminate = User.objects.get(username=request.data['username'], password=pwd)
                user_to_eliminate.delete()
            return Response(status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response(status=status.HTTP_409_CONFLICT)


# ----------------------------------------------------------------------------------
# from now, testing part

def get_cocktail_from_API(ingredient_list):
    # Use https://www.thecocktaildb.com/api/json/v1/1/filter.php?i='ingredient' for get possible Cocktails
    # Send Back JSON with list of Cocktails containing (Cocktailname, Picture, Ingredients, Recipe, ID)
    json_template = []
    for ingredient in ingredient_list:
        response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=" + str(ingredient))
        try:
            data = response.json()
        except ValueError:
            continue
        for cocktail in data["drinks"]:
            if(CocktailBlacklist.objects.filter(cocktail_id = cocktail["idDrink"]).exists()):
                continue
            cocktail_template = {"name": "", "picture": "", "id": ""}
            cocktail_template["name"] = cocktail["strDrink"]
            cocktail_template["picture"] = cocktail["strDrinkThumb"]
            cocktail_template["id"] = cocktail["idDrink"]
            if(Review.objects.filter(cocktail_id=cocktail_template["id"]).exists() and Review.objects.filter(cocktail_id=cocktail_template["id"]).values('is_personal_cocktail') == False):
                cocktail_template["rating"] = Review.objects.filter(cocktail_id=cocktail_template["id"]).aggregate(Avg('rating'))['rating']
            if(cocktail_template not in json_template):
                json_template.append(cocktail_template.copy())
    return json_template

def get_cocktail_from_DB(ingredient_list):
    json_template = []
    cocktail_template = {"name": "", "picture": "", "id": "", "user" : ""}

    for ingredient in ingredient_list:
        if(IngredientsList.objects.filter(name=str(ingredient)).exists()):
            ingredient_object = IngredientsList.objects.filter(name=str(ingredient))[0]
        else: continue
        
        for cocktail in PersonalCocktail.objects.all():
            cocktail_template = {"name": "", "picture": "", "id": ""}
            if(ingredient_object in cocktail.ingredients.all()):
                cocktail_template["name"] = cocktail.name
                cocktail_template["picture"] = cocktail.picture
                cocktail_template["id"] = cocktail.id
                cocktail_template["user"] = cocktail.user_id.username
                if(Review.objects.filter(cocktail_id=cocktail_template["id"]).exists() and Review.objects.filter(cocktail_id=cocktail_template["id"]).values('is_personal_cocktail') == True):
                    cocktail_template["rating"] = Review.objects.filter(cocktail_id=cocktail_template["id"]).aggregate(Avg('rating'))['rating']
                if(cocktail_template not in json_template):
                    json_template.append(cocktail_template.copy())
    return json_template

def cocktail_information(id):
    cocktail_template = {"name": "", "picture": "", "id": "", "description" : "", "recipe" : "", "user" : ""}
    ingredients = {}
    if(PersonalCocktail.objects.filter(id=id).exists()):
        cocktail = PersonalCocktail.objects.filter(id=id)[0]
        cocktail_template["name"] = cocktail.name
        cocktail_template["picture"] = cocktail.picture
        cocktail_template["id"] = id
        cocktail_template["recipe"] = cocktail.recipe
        cocktail_template["description"] = cocktail.description
        cocktail_template["username"] = cocktail.user_id.username
        cocktail_template["user_id"] = cocktail.user_id.id
        for i in cocktail.ingredients.all():
            ingredients[i.name] = CocktailIngredients.objects.filter(cocktail_id = id).values("centiliters")[0]
        cocktail_template["ingredients"] = ingredients
        if(Review.objects.filter(cocktail_id=id).exists()):
            cocktail_template["rating"] = Review.objects.filter(cocktail_id=id).aggregate(Avg('rating'))['rating']
        return cocktail_template
    else:
        cocktail_template = {"name": "", "picture": "", "id": ""}
        response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i=" + str(id))
        try:
            data = response.json()
        except ValueError:
            return []
        if data["drinks"] == None:
            return []
        cocktail_data = data["drinks"][0]
        cocktail_template["name"] = cocktail_data["strDrink"]
        cocktail_template["picture"] = cocktail_data["strDrinkThumb"]
        cocktail_template["id"] = id
        cocktail_template["recipe"] = cocktail_data["strInstructions"]
        for i in range(15):
            if(cocktail_data["strIngredient"+str(i+1)] != None):
                ingredients[cocktail_data["strIngredient"+str(i+1)]] = cocktail_data["strMeasure"+str(i+1)]
        cocktail_template["ingredients"] = ingredients
        return cocktail_template

def user_cocktails(uid):
    cocktail_template = {"user_id" : str(uid), "user_cocktails" : []}
    if uid == None:
        cocktail_template = {"user_cocktails" : []}
        for cocktail in PersonalCocktail.objects.all():
            cocktail_template["user_cocktails"].append(cocktail_information(cocktail.id))
        return cocktail_template
    if(PersonalCocktail.objects.filter(user_id=uid).exists()):
        for cocktail in PersonalCocktail.objects.filter(user_id=uid):
            cocktail_template["user_cocktails"].append(cocktail_information(cocktail.id))
        return cocktail_template
    else:
        return []

@api_view(['GET'])
def cocktails_by_ingredients(request):
    ingredients = request.GET["ingredients"].split(",")
    ingredients = [i.strip() for i in ingredients]
    json_template = {"cocktails_DB" : get_cocktail_from_DB(ingredients), "cocktails_API" : get_cocktail_from_API(ingredients)}
    return Response(data=json.dumps(json_template))

@api_view(['GET'])
def cocktail_by_information(request):
    id = int(request.GET["id"])
    json_template = cocktail_information(id)
    return Response(data=json.dumps(json_template))

@api_view(['GET'])
def test(request):
    return Response(user_cocktails(3))
