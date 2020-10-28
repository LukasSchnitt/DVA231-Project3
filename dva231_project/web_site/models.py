from django.db import models


class User(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=64)
    is_moderator = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)


class IngredientsList(models.Model):
    name = models.CharField(max_length=50)


class PersonalCocktail(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    blacklisted = models.BooleanField(default=False)
    description = models.CharField(max_length=500)
    picture = models.CharField(max_length=25)
    recipe = models.TextField()
    alcoholic = models.BooleanField(default=False)
    ingredients = models.ManyToManyField(IngredientsList, through='CocktailIngredients',
                                         through_fields=('cocktail_id', 'ingredient_id'))


class CocktailIngredients(models.Model):
    cocktail_id = models.ForeignKey(PersonalCocktail, on_delete=models.CASCADE)
    ingredient_id = models.ForeignKey(IngredientsList, on_delete=models.CASCADE)
    centiliters = models.FloatField()


class NotifyCocktail(models.Model):
    cocktail_id = models.ForeignKey(PersonalCocktail, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)


class Review(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    cocktail_id = models.IntegerField()
    is_personal_cocktail = models.BooleanField(default=True)
    rating = models.FloatField()
    comment = models.CharField(max_length=500)


class BookmarkedCocktail(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    cocktail_id = models.IntegerField()
    is_personal_cocktail = models.BooleanField()


class CocktailBlacklist(models.Model):
    cocktail_id = models.IntegerField()
    is_personal_cocktail = models.BooleanField()