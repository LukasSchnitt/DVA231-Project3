from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
# from .models import User, BookmarkedCocktail
from .serializers import UserSerializer, BookmarkSerializer
import hashlib
# -----------------------------------------------------
import requests
import json
from .models import *
from django.db.models import Avg
from django.shortcuts import render

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

    template_name = 'web_site/index.html'
    return render(request, template_name)





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


"""
    Cocktail Functions below

    Local function: get_cocktail_from_api_by_id (https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i='id')
    Return Description of a Cocktail (Cocktail Card) with a specific ID form the Cocktail-API if it exists there
    @param cocktail_id : integer cocktail id 
    @returns: dictionary containing 'id'=@param id, 'image', 'name',
    returns also average rating 'rating' of the reviews if there exists at least one review for it
"""

def get_cocktail_from_api_by_id(id):
    cocktail_template = {"name": "", "picture": "", "id": ""}
    response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i=" + str(id))
    try:
            data = response.json()
    except ValueError:
        return {}
    cocktail_data = data["drinks"][0]
    cocktail_template["name"] = cocktail_data["strDrink"]
    cocktail_template["picture"] = cocktail_data["strDrinkThumb"]
    cocktail_template["id"] = id
    if(Review.objects.filter(cocktail_id=id).exists() and Review.objects.filter(cocktail_id=cocktail_template["id"]).values('is_personal_cocktail') == False):
        cocktail_template["rating"] = Review.objects.filter(cocktail_id=id).aggregate(Avg('rating'))['rating']
    return cocktail_template


"""
    Local function: get_cocktail_from_db_by_id 
    Return Description of a Cocktail (Cocktail Card) with a specific ID form the Database if it exists there
    @param cocktail_id : integer cocktail id 
    @returns : dictionary containing 'id'=@param id, 'image', 'name',
    returns also average rating 'rating' of the reviews if there exists at least one review for it
"""

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


"""
    Local function: get_cocktail_from_API (https://www.thecocktaildb.com/api/json/v1/1/filter.php?i='ingredient')
    Return Description of a Cocktails (Cocktail Card) which contains at least one of the ingredients
    @param ingredient_list : list of ingredients (strings)
    @returns: list of cocktail-dictionarys containing 'id', 'image', 'name',
    returns also average rating 'rating' of the reviews in the cocktial dictionary if there exists at least one review for it
"""

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


"""
    Local function: get_cocktail_from_DB
    Return Description of a Cocktails (Cocktail Card) which contains at least one of the ingredients
    @param ingredient_list : list of ingredients (strings)
    @returns: list of cocktail-dictionarys containing 'id', 'image', 'name',
    returns also average rating 'rating' of the reviews in the cocktial dictionary if there exists at least one review for it
"""

def get_cocktail_from_DB(ingredient_list, alcoholic):
    json_template = []
    cocktail_template = {"name": "", "picture": "", "id": "", "user" : ""}

    for ingredient in ingredient_list:
        if(IngredientsList.objects.filter(name=str(ingredient)).exists()):
            ingredient_object = IngredientsList.objects.filter(name=str(ingredient))[0]
        else: continue

        if(alcoholic == True):
            cocktail_list = PersonalCocktail.objects.filter(alcoholic=True)
        elif(alcoholic == False):
            cocktail_list = PersonalCocktail.objects.filter(alcoholic=True)
        else:
            cocktail_list = PersonalCocktail.objects.all()

        for cocktail in cocktail_list:
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


"""
    Local function: cocktail_information
    Return full Description of a Cocktail from the Database, if there are no Cocktail in the Database which matches the ID
    then the Cocktail-API will be requested (https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i='id')
    @param id : id of the Cocktial
    @returns: list of cocktail-dictionarys containing 'id', 'image', 'name', 'recipe', 'description', 'username', 'user-id', 'ingredients'
    returns also average rating 'rating' of the reviews in the cocktial dictionary if there exists at least one review for it
"""

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
        if(Review.objects.filter(cocktail_id=id).exists()):
            cocktail_template["rating"] = Review.objects.filter(cocktail_id=id).aggregate(Avg('rating'))['rating']
        return cocktail_template


"""
    Local function: user_cocktail
    Return  Description of all Cocktails (Cocktail-Cards) from a specific user(user-id) in the Database
    @param uid : integer id of the user
    @returns: dictionary with user-id and a list of cocktail-dictionarys containing 'id', 'image', 'name', 'recipe', 'description', 'username', 'user-id', 'ingredients'
    returns also average rating 'rating' of the reviews in the cocktial dictionary if there exists at least one review for it 
    (Calls cocktail_information function for each cocktail-id from the user-cocktails)
"""

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
        return {}

"""
    API-function: cocktails_by_ingredients
    @param uid : request from the Website (List of ingredients), alcoholic-FLag for getting all alcoholic(True), non-alcoholic(False)
    or all Cocktails(None) from the Database
    @returns: JSON-String for the Website which contains list of API and DB cocktails which contain the ingredients
    (Calls local get_cocktail_from_DB and get_cocktail_from_API functions)
"""

@api_view(['GET'])
def cocktails_by_ingredients(request):
    ingredients = request.GET["ingredients"].split(",")
    ingredients = [i.strip() for i in ingredients]
    json_template = {"cocktails_DB" : get_cocktail_from_DB(ingredients, alcoholic=None), "cocktails_API" : get_cocktail_from_API(ingredients)}
    return Response(data=json.dumps(json_template))


"""
    API-function: cocktails_by_information
    @param uid : request from the Website (id of requested Cocktail)
    @returns: JSON-String for the Website full description of a Cocktail
    (Calls local cocktail_information function)
"""

@api_view(['GET'])
def cocktail_by_information(request):
    id = int(request.GET["id"])
    json_template = cocktail_information(id)
    return Response(data=json.dumps(json_template))
