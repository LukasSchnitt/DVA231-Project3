import requests
import json

response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/filter.php?i=bla")
try:
    responses = response.json()
    print(response.json())
except ValueError:
    print("JSON-Empty")



    
