from django.db import models


# Create your models here.
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
    description = models.CharField(max_length=500)
    picture = models.CharField(max_length=25)
    recipe = models.TextField()
    ingredients = models.ManyToManyField(IngredientsList, through='CocktailIngredients',
                                         through_fields=('cocktail_id', 'ingredient_id'))


class CocktailIngredients(models.Model):
    cocktail_id = models.ForeignKey(PersonalCocktail, on_delete=models.CASCADE)
    ingredient_id = models.ForeignKey(IngredientsList, on_delete=models.CASCADE)
    centiliters = models.FloatField()


class Review(models.Model):
    class RatingValue(models.IntegerChoices):
        BAD = 1
        OK = 2
        GOOD = 3
        AWESOME = 4
        PERFECT = 5

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    cocktail_id = models.IntegerField()
    is_personal_cocktail = models.BooleanField()
    rating = models.IntegerField(default=RatingValue.PERFECT, choices=RatingValue.choices)
    comment = models.CharField(max_length=500)


class BookmarkedCocktail(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    cocktail_id = models.IntegerField()
    is_personal_cocktail = models.BooleanField()


class CocktailBlacklist(models.Model):
    cocktail_id = models.IntegerField()
    is_personal_cocktail = models.BooleanField()
