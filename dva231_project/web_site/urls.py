from django.urls import path
from . import views


urlpatterns = [
    path('', views.home),
    path('user', views.user),
    path('bookmark', views.bookmark),
    path('review', views.review, name='urlname'),
    path('personal_cocktail', views.personal_cocktail),
    path('cocktail_information', views.cocktail_by_information, name = 'urlname'),
    path('cocktail_by_ingredients', views.cocktails_by_ingredients, name = 'urlname')
]
