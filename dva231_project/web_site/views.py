import base64
import hashlib
import json
import os
from datetime import datetime
from random import getrandbits, choice

import requests
from django.db.models import Avg
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import *


def home(request):
    if 'is_logged_in' in request.session and 'is_moderator' in request.session and \
            request.session['is_logged_in'] and request.session['is_moderator']:
        user_id = request.session['id']
        return render(request, 'web_site/index_moderator.html',
                      {"is_authenticated": True, "user_id": user_id, 'is_moderator': True})
    elif 'is_logged_in' in request.session and request.session['is_logged_in']:
        user_id = request.session['id']
        return render(request, 'web_site/index_user.html', {"is_authenticated": True, "user_id": user_id})

    template_name = 'web_site/index.html'
    return render(request, template_name)


def profile(request):
    template_name = 'web_site/profile.html'
    if (not ('is_logged_in' in request.session)) or (not request.session['is_logged_in']):
        return render(request, 'web_site/index.html')

    user_id = request.session['id']
    return render(request, template_name, {"user_id": user_id,
                                           'is_authenticated': True,
                                           'is_moderator': 'is_moderator' in request.session and request.session[
                                               'is_moderator']})


def mod(request):
    template_name = 'web_site/mod.html'
    return render(request, template_name)


@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def cocktail_API(request):
    if request.method == 'GET':
        if 'ingredients' in request.GET:
            return cocktails_by_ingredients(request)
        if 'id' in request.GET and 'is_personal_cocktail' in request.GET:
            return cocktail_by_information(request)
        if 'random' in request.GET and request.GET['random']:
            return random_cocktail()
    return personal_cocktail(request)


'''
    This API works only for users that are logged in, otherwise:
        @returns HTTP STATUS 401
    Allowed Request Methods:
        - GET : used to retrieve the notifications list
                @returns a list containing
                        cocktail_id : integer unique identifier of the personal cocktail
                        notification_id : integer unique identifier of the notification 
        - POST : used to confirm that the user have seen the notification
                @param notifications : array containing all the notification_id to confirm
                @returns HTTP STATUS 200 after all notifications have been confirmed
'''


@api_view(['GET', 'POST'])
def notifications(request):
    if not ('is_logged_in' in request.session and request.session['is_logged_in']):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'GET':
        return notifications_list(request.session['id'])
    elif request.method == 'POST':
        return notifications_confirm(request.data['notifications'])
    return Response(status=status.HTTP_409_CONFLICT)

'''
    This function checks for a specififc user, which Personal-Cocktails of him are blacklisted and therefore 
    he should be informed about the cocktails in the front-end
    Input: User-ID
    Output: List of Cocktail which are the user get Notified about, because they are Blacklisted
'''
def notifications_list(user_id):
    cocktail_list = user_cocktails(user_id)
    out = []
    if not cocktail_list['blacklist_cocktails']:
        return Response(data=out)
    for cocktail in cocktail_list['blacklist_cocktails']:
        elem = NotifyCocktail.objects.get(cocktail_id=cocktail['id'])
        if not elem.confirmed:
            out.append({
                'cocktail_id': cocktail['id'],
                'notification_id': elem.id
            })
    return Response(data=out)

'''
    This function confirmed the given notification from a user and saved the confirmation of that in the Database,
    so that the System "knows" that the User got the notification
    Input: List of notifications
    Output: Status code for correct work of function
'''

def notifications_confirm(confirmed_notifications):
    for notification in confirmed_notifications:
        element = NotifyCocktail.objects.get(id=notification)
        element.confirmed = True
        element.save()
    return Response(status=status.HTTP_200_OK)


'''
    This API works only for users that are logged in, otherwise:
        @returns HTTP STATUS 401
    Allowed Request Methods:
        - GET : used to retrieve the personal cocktail list
            @returns HTTP STATUS 404 there are no personal cocktail
            if the user is moderator:
                @returns a json containing all the personal cocktails
                            every element of the json contains:
                                ... To DO
            otherwise:
                @returns a json containing all the user personal cocktails
                            every element of the json contains 
                                ... To DO
        - POST : used to add a personal cocktail
            @param name : string name of the cocktail (max 50 characters)
            @param description : string description of the cocktail (max 500 characters)
            @param recipe : string recipe of the cocktail
            @param img : byte content of the cocktail image
            @param extension : string extension of the original image
            @param ingredients : dictionary containing
                                    @param name : string name of the ingredient
                                    @param centiliters : double quantity of that ingredient in centiliters
            @returns HTTP STATUS 201 if personal cocktail has been added correctly
            @returns HTTP STATUS 400 if data are not valid
        - PATCH : used to edit an existing personal cocktail
            @param cocktail_id : integer unique identifier of the cocktail
            depending on what have to be changed one or more of:
                @param name : string (max 50 characters)
                @param description : string (maximum 500 characters)
                @param recipe : string 
                @param image : byte (also requires @param extension)
                @param extension : string
                @param ingredients : dictionary (when updating the ingredients all ingredients will be replaced)
                                    every element of the dictionary must contain:
                                    @param name : string
                                    @param centiliters : double
            @returns HTTP STATUS 200 if the personal cocktail has been changed correctly
            @returns HTTP STATUS 400 if data are not changed
            @returns HTTP STATUS 404 if data are not valid
        - DELETE : use to delete an existing review
            if the user is a moderator:
                @param cocktail_id : integer unique identifier of the personal cocktail 
                                        (if this parameter is not given then a normal DELETE will be done)
            else:
                @param id : integer unique identifier of the personal cocktail
            @returns HTTP STATUS 200 if the review has been deleted successfully
            @returns HTTP STATUS 404 if the data are not valid
'''

'''
    This function check for the method which will be executed in terms of the Personal Cocktail
    Options are: List the Personal-Cocktails, Add a Personal Cocktail, edit a Personal-Cocktail and delete a Personal Cocktail.
    Its only possible for User who are Logged in.
    Input: Request which contain Booled for checking if a user is logged in and either depending on the Request-Method:
        GET: User-ID for identifying the Users-Cocktail
        POST: User-ID, Name of Cocktail, Recipe, Image and list of ingredients for adding a Personal-Cocktail
        PATCH: Cocktail-ID for identifying the editing Cocktail, Name, Recipe, Image and list of ingredients for editing existing Cocktail
        DELETE: Cocktail-ID for identifying the deleting Cocktail        
    Output: Statuscode for checking if the performed action was sucessful
'''

def personal_cocktail(request):
    if not ('is_logged_in' in request.session and request.session['is_logged_in']):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'GET':
        return personal_cocktail_list(request)
    elif request.method == 'POST':
        return personal_cocktail_add(request)
    elif request.method == 'PATCH':
        return personal_cocktail_edit(request)
    elif request.method == 'DELETE':
        return personal_cocktail_delete(request)
'''
    This function returns a list of Cocktails, if the user is not a moderator (empty list then)
    Input: User-ID in request
    Output: List of Cocktails which the user creates
'''

def personal_cocktail_list(request):
    try:
        if 'is_moderator' in request.session and request.session['is_moderator']:
            out = user_cocktails(None)
        else:
            out = user_cocktails(request.session['id'])
        return Response(data=out)
    except PersonalCocktail.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

'''
    This function checks add a Cocktail to the Database for a specific user
    Input: User-ID, Name, Recipe, Image and Ingredient-List for adding a Cocktial
    Output: Statuscode if the adding-process was sucessful or not
'''

def personal_cocktail_add(request):
    now = datetime.now()
    img_url = str(now.year) + str(now.month) + str(now.day) + str(now.hour) + str(now.minute) + str(now.second) + \
        str(now.microsecond) + '.' + request.data['extension']
    data_for_serializer = {
        'user_id': request.session['id'],
        'name': request.data['name'],
        'description': request.data['description'],
        'picture': img_url,
        'recipe': request.data['recipe']
    }
    print(data_for_serializer)
    serializer = PersonalCocktailSerializer(data=data_for_serializer)
    if serializer.is_valid():
        print("in")
        serializer.save()
        cocktail_id = PersonalCocktail.objects.get(user_id=request.session['id'], name=request.data['name'],
                                                   description=request.data['description'], picture=img_url,
                                                   recipe=request.data['recipe']).id
        data = json.loads(request.data['ingredients'])
        for ingredient in data.keys():
            result, ingredient_id = personal_cocktail_add_ingredient(ingredient)
            if result == status.HTTP_200_OK:
                result = personal_cocktail_add_ingredient_to_cocktail(cocktail_id, ingredient_id, data[ingredient])

            if result == status.HTTP_400_BAD_REQUEST:
                cocktail = PersonalCocktail.objects.get(id=cocktail_id)
                cocktail.delete()
                return Response(status=status.HTTP_400_BAD_REQUEST)
        result = personal_cocktail_add_image(request.session['id'], img_url, request.data['img'])
        return Response(status=result)
    return Response(status=status.HTTP_400_BAD_REQUEST)

'''
    This function adds a specific ingredient to the Ingredient-Table in the Database
    Input: ingredientname
    Output: Statuscode if the Process of adding a new ingredient was sucessful or not
'''

def personal_cocktail_add_ingredient(ingredient_name):
    try:
        ingredient_id = IngredientsList.objects.get(name=ingredient_name).id
        return status.HTTP_200_OK, ingredient_id
    except IngredientsList.DoesNotExist:
        data_for_serializer = {
            'name': ingredient_name
        }
        serializer = IngredientsListSerializer(data=data_for_serializer)
        if serializer.is_valid():
            serializer.save()
            ingredient_id = IngredientsList.objects.get(name=ingredient_name).id
            return status.HTTP_200_OK, ingredient_id
    return status.HTTP_400_BAD_REQUEST, -1

'''
    This function adds a many-to-many-relation between a Cocktail and a specific Ingredient including the measurement of it
    Input: ingredient-id, cocktail-id and ingredient_centiliters
    Output: Statuscode if the Process of adding a new ingredient to a Cocktail was sucessful or not
'''

def personal_cocktail_add_ingredient_to_cocktail(cocktail_id, ingredient_id, ingredient_centiliters):
    data_for_serializer = {
        'cocktail_id': cocktail_id,
        'ingredient_id': ingredient_id,
        'centiliters': ingredient_centiliters
    }
    serializer = CocktailIngredientsSerializer(data=data_for_serializer)
    if serializer.is_valid():
        serializer.save()
        return status.HTTP_200_OK
    return status.HTTP_400_BAD_REQUEST

'''
    This function adds a image for a specific Cocktial to the database
    Input: user-id, img-url, image
    Output: Statuscode if the Process of adding a new image to the directory was sucessful or not
'''

def personal_cocktail_add_image(user_id, img_url, image):
    if not os.path.exists("web_site/static/web_site/img/cocktail/" + str(user_id)):
        os.makedirs("web_site/static/web_site/img/cocktail/" + str(user_id))
    with open("web_site/static/web_site/img/cocktail/" + str(user_id) + img_url, "wb") as f:
        image = image.split(',')[1].encode()
        f.write(base64.decodebytes(image))
    return status.HTTP_201_CREATED

'''
    This function edit the properties of an existing Cocktail in the Database
    Input: User-Id, Cocktail-ID, Name, Recipe, image and List of Ingredients
    Output: Statuscode if the Process of editing the Cocktail was sucessful or not
'''

def personal_cocktail_edit(request):
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
            img_url = str(now.year) + str(now.month) + str(now.day) + str(now.hour) + str(now.minute) + \
                      str(now.second) + str(now.microsecond) + request.data['extension']
            personal_cocktail_add_image(request.session['id'], img_url, request.data['img'])
            cocktail_to_edit.picture = img_url
        if 'ingredients' in request.data:
            for row in CocktailIngredients.objects.filter(cocktail_id=request.data['cocktail_id']):
                row.delete()
            for ingredient in request.data['ingredients']:
                response, ingredient_id = personal_cocktail_add_ingredient(ingredient['name'])
                if response == status.HTTP_200_OK:
                    response = personal_cocktail_add_ingredient_to_cocktail(request.data['cocktail_id'], ingredient_id,
                                                                            ingredient['centiliters'])
                if response == status.HTTP_400_BAD_REQUEST:
                    cocktail = PersonalCocktail.get(id=request.data['cocktail_id'])
                    cocktail.delete()
                    return Response(status=status.HTTP_400_BAD_REQUEST)
        if edited:
            cocktail_to_edit.save()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except PersonalCocktail.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

'''
    This function adds a banned Cocktail to the Database-Table Blacklisted-Cocktails
    Input: Cocktial-ID
    Output: Statuscode if the Process of banning the Cocktail was sucessful or not
'''

def ban_cocktail(cocktail_id):
    data_for_serializer = {
        "cocktail_id": cocktail_id,
        "is_personal_cocktail": False
    }
    serializer = CocktailBlacklistSerializer(data=data_for_serializer)
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)

'''
    This function deletes a specific Cocktial from the Database-Table and sends a notification to the user
    Input: Cocktail-ID, User-ID
    Output: Statuscode if the Process of deleting the Cocktail was sucessful or not
'''

def personal_cocktail_delete(request):
    try:
        if 'is_moderator' in request.session and request.session['is_moderator'] \
                and 'cocktail_id' in request.data and 'is_personal_cocktail' in request.data:
            if not bool(int(request.data['is_personal_cocktail'])):
                return ban_cocktail(request.data['cocktail_id'])
            user_cocktail = PersonalCocktail.objects.get(id=request.data['cocktail_id'])
            user_cocktail.blacklisted = not user_cocktail.blacklisted
            if user_cocktail.blacklisted:
                data_for_serializer = {
                    'cocktail_id': request.data['cocktail_id']
                }
                serializer = NotifyCocktailSerializer(data=data_for_serializer)
                if not serializer.is_valid():
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                serializer.save()
            else:
                notification = NotifyCocktail.objects.get(cocktail_id=request.data['cocktail_id'])
                notification.delete()
            user_cocktail.save()
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
        return review_list(request)
    if not ('is_logged_in' in request.session and 'id' in request.session and request.session['is_logged_in']):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'POST':
        return review_add(request)
    elif request.method == 'PATCH':
        return review_edit(request)
    elif request.method == 'DELETE':
        return review_delete(request)

'''
    This function returns a list of all existing reviews regarding to a specific Cocktial
    Input: Cocktial-ID, Boolean if it is a personal-cocktial or not
    Output: List of all regarding Review-Objects for a specific Cocktail and a Statuscode for checking if the process
    was sucessful or not
'''

def review_list(request):
    try:
        cocktail_reviews = Review.objects.filter(cocktail_id=request.GET['cocktail_id'],
                                                 is_personal_cocktail=request.GET['is_personal_cocktail']) \
            .values('id', 'user_id', 'rating', 'comment')
        out = []
        for user_review in cocktail_reviews:
            out.append({
                'id': user_review['id'],
                'user_id': user_review['user_id'],
                'username': User.objects.get(id=user_review['user_id']).username,
                'rating': user_review['rating'],
                'comment': user_review['comment']
            })
        return Response(data=out)
    except Review.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

'''
    This function adds a specific ingredient to the Ingredient-Table in the Database
    Input: ingredientname
    Output: Statuscode if the Process of adding a new ingredient was sucessful or not
'''

def review_add(request):
    try:
        Review.objects.get(user_id=request.session['id'], cocktail_id=request.data['cocktail_id'])
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
    except Review.DoesNotExist:
        pass
    if float(request.data['rating']) > 5 or float(request.data['rating']) < 0:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    data_for_serializer = {
        'user_id': request.session['id'],
        'cocktail_id': request.data['cocktail_id'],
        'is_personal_cocktail': bool(int(request.data['is_personal_cocktail'])),
        'rating': request.data['rating'],
        'comment': request.data['comment']
    }
    serializer = ReviewSerializer(data=data_for_serializer)
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
    return Response(status=status.HTTP_400_BAD_REQUEST)


def review_edit(request):
    try:
        user_review = Review.objects.get(id=request.data['id'], user_id=request.session['id'])
        changed = False
        if 'rating' in request.data:
            if float(request.data['rating']) > 5 or float(request.data['rating']) < 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)
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


def review_delete(request):
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
    Cocktail Functions below

    Local function: get_cocktail_from_api_by_id (https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i='id')
    Return Description of a Cocktail (Cocktail Card) with a specific ID form the Cocktail-API if it exists there
    @param cocktail_id : integer cocktail id 
    @returns: dictionary containing 'id'=@param id, 'image', 'name',
    returns also average rating 'rating' of the reviews if there exists at least one review for it
'''


def get_cocktail_from_api_by_id(cocktail_id):
    if CocktailBlacklist.objects.filter(cocktail_id=cocktail_id).exists():
        return []
    response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i=" + str(cocktail_id))
    try:
        data = response.json()
    except ValueError:
        return []
    if data["drinks"] is None:
        return []
    cocktail_data = data["drinks"][0]
    cocktail_template = {
        "name": cocktail_data["strDrink"],
        "picture": cocktail_data["strDrinkThumb"],
        "id": cocktail_id,
        "recipe": cocktail_data["strInstructions"],
        'is_personal_cocktail': 0
    }
    ingredients = {}
    for i in range(15):
        if cocktail_data["strIngredient" + str(i + 1)] is not None:
            ingredients[cocktail_data["strIngredient" + str(i + 1)]] = cocktail_data["strMeasure" + str(i + 1)]
    cocktail_template["ingredients"] = ingredients
    reviews = Review.objects.filter(cocktail_id=cocktail_id, is_personal_cocktail=False)
    if reviews:
        cocktail_template["rating"] = reviews.aggregate(Avg('rating'))['rating__avg']
    return cocktail_template


"""
    Local function: get_cocktail_from_db_by_id 
    Return Description of a Cocktail (Cocktail Card) with a specific ID form the Database if it exists there
    @param cocktail_id : integer cocktail id 
    @returns : dictionary containing 'id'=@param id, 'image', 'name',
    returns also average rating 'rating' of the reviews if there exists at least one review for it
"""


def get_cocktail_from_db_by_id(cocktail_id):
    cocktail = PersonalCocktail.objects.get(id=cocktail_id)
    if not cocktail:
        return []
    cocktail_template = {
        "name": cocktail.name,
        "picture": 'static/web_site/img/cocktail/' + str(cocktail.user_id.id) + cocktail.picture,
        "id": cocktail_id,
        "recipe": cocktail.recipe,
        "description": cocktail.description,
        "username": cocktail.user_id.username,
        "user_id": cocktail.user_id.id,
        'is_personal_cocktail': 1
    }
    ingredients = {}
    for i in cocktail.ingredients.all():
        ingredients[i.name] = CocktailIngredients.objects.get(cocktail_id=cocktail_id, ingredient_id=i.id).centiliters
    cocktail_template["ingredients"] = ingredients
    reviews = Review.objects.filter(cocktail_id=cocktail_id, is_personal_cocktail=True)
    if reviews:
        cocktail_template["rating"] = reviews.aggregate(Avg('rating'))['rating__avg']
    return cocktail_template


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
            @returns HTTP STATUS 201    if cocktail has been added
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
    if request.method == 'GET':
        return bookmark_list(request.session['id'])
    elif request.method == 'POST':
        return bookmark_add(request.session['id'], request.data['cocktail_id'], request.data['is_personal_cocktail'])
    elif request.method == 'DELETE':
        return bookmark_delete(request.session['id'], request.data['cocktail_id'], request.data['is_personal_cocktail'])


def bookmark_list(user_id):
    try:
        user_bookmarks = BookmarkedCocktail.objects.filter(user_id=user_id) \
            .values('cocktail_id', 'is_personal_cocktail')
        response = []
        for row in user_bookmarks:
            if not row['is_personal_cocktail']:
                response.append(get_cocktail_from_api_by_id(row['cocktail_id']))
            else:
                response.append(get_cocktail_from_db_by_id(row['cocktail_id']))
        return Response(data=response)
    except BookmarkedCocktail.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


def bookmark_add(user_id, cocktail_id, is_personal_cocktail):
    data_for_serializer = {
        'user_id': user_id,
        'cocktail_id': cocktail_id,
        'is_personal_cocktail': is_personal_cocktail
    }
    serializer = BookmarkSerializer(data=data_for_serializer)
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
    return Response(status=status.HTTP_400_BAD_REQUEST)


def bookmark_delete(user_id, cocktail_id, is_personal_cocktail):
    try:
        bookmark_to_eliminate = BookmarkedCocktail.objects.get(
            user_id=user_id,
            cocktail_id=cocktail_id,
            is_personal_cocktail=is_personal_cocktail
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
    elif request.method == 'HEAD':
        return user_logout(request)
    elif request.method == 'POST':
        return user_login(request)
    elif request.method == 'PUT':
        return user_signup(request)
    elif request.method == 'DELETE':
        return user_delete(request)
    return Response(status=status.HTTP_409_CONFLICT)


def user_logout(request):
    if 'is_logged_in' in request.session and request.session['is_logged_in']:
        del request.session['is_logged_in']
        del request.session['is_moderator']
        del request.session['id']
        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)


def user_login(request):
    try:
        pwd = hashlib.sha256(request.data['password'].encode()).hexdigest()
        user_entry = User.objects.get(username=request.data['username'], password=pwd)
        if user_entry.is_banned:
            return Response(status=status.HTTP_403_FORBIDDEN)
        request.session['is_logged_in'] = True
        request.session['is_moderator'] = user_entry.is_moderator
        request.session['id'] = user_entry.id
        return Response(status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


def user_signup(request):
    try:
        User.objects.get(username=request.data['username'])
        return Response(status=status.HTTP_226_IM_USED)
    except User.DoesNotExist:
        data_for_serializer = {
            'username': request.data['username'],
            'password': hashlib.sha256(request.data['password'].encode()).hexdigest(),
            'is_moderator': (request.data['moderator'] if 'is_moderator' in request.data else False),
            'is_banned': (request.data['is_banned'] if 'is_banned' in request.data else False)
        }
        serializer = UserSerializer(data=data_for_serializer)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
    return Response(status=status.HTTP_400_BAD_REQUEST)


def user_delete(request):
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


"""
    Local function: get_cocktail_from_API (https://www.thecocktaildb.com/api/json/v1/1/filter.php?i='ingredient')
    Return Description of a Cocktails (Cocktail Card) which contains at least one of the ingredients
    @param ingredient_list : list of ingredients (strings)
    @returns: list of cocktail-dictionaries containing 'id', 'image', 'name',
    returns also average rating 'rating' of the reviews in the cocktail dictionary if there exists at least one review 
    for it
"""


def get_cocktail_from_API_by_ingredients(ingredient_list):
    json_template = []
    for ingredient in ingredient_list:
        response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=" + str(ingredient))
        try:
            data = response.json()
        except ValueError:
            continue
        for cocktail in data["drinks"]:
            if not CocktailBlacklist.objects.filter(cocktail_id=cocktail["idDrink"]).exists():
                cocktail_template = {
                    "name": cocktail["strDrink"],
                    "picture": cocktail["strDrinkThumb"],
                    "id": cocktail['idDrink']
                }
                reviews = Review.objects.filter(cocktail_id=cocktail['idDrink'], is_personal_cocktail=False)
                if reviews:
                    cocktail_template["rating"] = reviews.aggregate(Avg('rating'))['rating__avg']
                if cocktail_template not in json_template:
                    json_template.append(cocktail_template.copy())
    return json_template


"""
    Local function: get_cocktail_from_DB
    Return Description of a Cocktails (Cocktail Card) which contains at least one of the ingredients
    @param ingredient_list : list of ingredients (strings)
    @returns: list of cocktail-dictionaries containing 'id', 'image', 'name',
    returns also average rating 'rating' of the reviews in the cocktail dictionary if there exists at least one review
    for it
"""


def get_cocktail_from_DB_by_ingredients(ingredient_list, alcoholic):
    json_template = []

    for ingredient in ingredient_list:
        try:
            ingredient_object = IngredientsList.objects.get(name=str(ingredient))
        except IngredientsList.DoesNotExist:
            continue
        if alcoholic is None:
            cocktail_list = PersonalCocktail.objects.all()
        elif alcoholic:
            cocktail_list = PersonalCocktail.objects.filter(alcoholic=True)
        elif not alcoholic:
            cocktail_list = PersonalCocktail.objects.filter(alcoholic=False)
        else:
            cocktail_list = PersonalCocktail.objects.all()

        for cocktail in cocktail_list:
            if cocktail.blacklisted:
                continue
            if ingredient_object in cocktail.ingredients.all():
                cocktail_template = {
                    "name": cocktail.name,
                    "picture": 'static/web_site/img/cocktail/' + str(cocktail.user_id.id) + cocktail.picture,
                    "id": cocktail.id,
                    "recipe": cocktail.recipe,
                    "description": cocktail.description,
                    "username": cocktail.user_id.username,
                    "user_id": cocktail.user_id.id
                }
                reviews = Review.objects.filter(cocktail_id=cocktail_template["id"], is_personal_cocktail=True)
                if reviews:
                    cocktail_template["rating"] = reviews.aggregate(Avg('rating'))['rating__avg']
                if cocktail_template not in json_template:
                    json_template.append(cocktail_template.copy())
    return json_template


"""
    Local function: cocktail_information
    Return full Description of a Cocktail from the Database, 
    if there are no Cocktail in the Database which matches the ID
    then the Cocktail-API will be requested (https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i='id')
    @param id : id of the cocktail
    @returns: list of cocktail-dictionaries containing 
                    'id', 
                    'image', 
                    'name', 
                    'recipe', 
                    'description', 
                    'username', 
                    'user-id', 
                    'ingredients'
    returns also average rating 'rating' of the reviews in the cocktail dictionary 
    if there exists at least one review for it
"""


def cocktail_information(cocktail_id, is_personal_cocktail):
    if is_personal_cocktail:
        cocktail_template = get_cocktail_from_db_by_id(cocktail_id)
    else:
        cocktail_template = get_cocktail_from_api_by_id(cocktail_id)
    return cocktail_template


"""
    Local function: user_cocktail
    Return  Description of all Cocktails (Cocktail-Cards) from a specific user(user-id) in the Database
    @param uid : integer id of the user
    @returns: dictionary with user-id and a list of cocktail-dictionaries containing 'id', 'image', 'name', 'recipe', 
                                                                'description', 'username', 'user-id', 'ingredients'
    returns also average rating 'rating' of the reviews in the cocktail dictionary 
                if there exists at least one review for it 
    (Calls cocktail_information function for each cocktail-id from the user-cocktails)
"""


def user_cocktails(uid):
    if uid is None:
        cocktail_template = {"user_cocktails": [], "blacklist_cocktails": []}
        for cocktail in PersonalCocktail.objects.all():
            cocktail_template["user_cocktails"].append(cocktail_information(cocktail.id, True))
        return cocktail_template
    if PersonalCocktail.objects.filter(user_id=uid).exists():
        cocktail_template = {"user_id": str(uid), "user_cocktails": []}
        for cocktail in PersonalCocktail.objects.filter(user_id=uid):
            if cocktail.blacklisted:
                cocktail_template["blacklist_cocktails"].append(cocktail_information(cocktail.id, True))
            else:
                cocktail_template["user_cocktails"].append(cocktail_information(cocktail.id, True))
        return cocktail_template
    return []


"""
    API-function: cocktails_by_ingredients
    @param uid : request from the Website (List of ingredients), 
                    alcoholic-FLag for getting all alcoholic(True), non-alcoholic(False)
    or all Cocktails(None) from the Database
    @returns: JSON-String for the Website which contains list of API and DB cocktails which contain the ingredients
    (Calls local get_cocktail_from_DB and get_cocktail_from_API functions)
"""


def random_cocktail_from_API():
    while True:
        response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/random.php")
        data = response.json()
        cocktail_data = data["drinks"][0]
        if not CocktailBlacklist.objects.filter(cocktail_id=cocktail_data['idDrink']).exists():
            break

    cocktail_template = {
        "name": cocktail_data["strDrink"],
        "picture": cocktail_data["strDrinkThumb"],
        "id": cocktail_data['idDrink'],
        "recipe": cocktail_data["strInstructions"]
    }
    ingredients = {}
    for i in range(15):
        if cocktail_data["strIngredient" + str(i + 1)] is not None:
            ingredients[cocktail_data["strIngredient" + str(i + 1)]] = cocktail_data["strMeasure" + str(i + 1)]
    cocktail_template["ingredients"] = ingredients
    reviews = Review.objects.filter(cocktail_id=cocktail_data['idDrink'], is_personal_cocktail=False)
    if reviews:
        cocktail_template["rating"] = reviews.aggregate(Avg('rating'))['rating__avg']
    return cocktail_template


def random_cocktail_from_DB():
    cocktails = PersonalCocktail.objects.filter(blacklisted=False)
    cocktail = choice(cocktails)
    return cocktail_information(cocktail.id, True)


def random_cocktail():
    if not bool(getrandbits(1)):
        json_template = {
            "random_cocktail": random_cocktail_from_DB(),
            "source": "DB"
        }
    else:
        json_template = {
            "random_cocktail": random_cocktail_from_API(),
            "source": "API"
        }
    return Response(data=json.dumps(json_template))


def cocktails_by_ingredients(request):
    ingredients = request.GET["ingredients"].split(",")
    ingredients = [i.strip() for i in ingredients]
    json_template = {
        "cocktails_DB": get_cocktail_from_DB_by_ingredients(ingredients, alcoholic=None),
        "cocktails_API": get_cocktail_from_API_by_ingredients(ingredients)
    }
    return Response(data=json.dumps(json_template))


"""
    API-function: cocktails_by_information
    @param uid : request from the Website (id of requested Cocktail)
    @returns: JSON-String for the Website full description of a Cocktail
    (Calls local cocktail_information function)
"""


def cocktail_by_information(request):
    cocktail_id = int(request.GET["id"])
    is_personal_cocktail = bool(int(request.GET['is_personal_cocktail']))
    json_template = cocktail_information(cocktail_id, is_personal_cocktail)
    return Response(data=json.dumps(json_template))


@api_view(['GET'])
def test(request):
    """
    for testing

    review = Review.objects.filter(id=1)
    data = {}
    data['review'] = review.aggregate(Avg('rating'))['rating__avg']
    return Response(data=json.dumps(data))
    """
    return Response(status=status.HTTP_204_NO_CONTENT)
