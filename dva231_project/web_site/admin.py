from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(PersonalCocktail)
admin.site.register(User)
admin.site.register(IngredientsList)
admin.site.register(CocktailIngredients)
admin.site.register(Review)
admin.site.register(BookmarkedCocktail)
admin.site.register(CocktailBlacklist)

