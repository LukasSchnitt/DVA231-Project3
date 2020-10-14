import requests
import json
import sys
from models import *


sys.path.append("/home/lukas/anaconda3/bin/")
#response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/search.php?s=margarita")

#response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=gin")
#object1 = response.json()
#response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=lemon")
#object2 = response.json()

    
def get_cocktailbyingredients(ingredient):
# Use https://www.thecocktaildb.com/api/json/v1/1/filter.php?i='ingredient' for get possible Cocktails     
# Send Back JSON with list of Cocktails containing (Cocktailname, Picture, Ingredients, Recipe, ID)
    json_template = { "cocktails" : [] }
    cocktail_template = {"name" : "", "picture" : "", "id" : "" }
    
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
    result1 = IngredientsList.objects.filter(name = ingredient)
    print(result1)
    

get_database_cocktails("ingredient1")   

    
