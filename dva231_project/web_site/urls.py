from . import views
from django.urls import path


urlpatterns = [
    path('', views.home),
    path('bookmark', views.bookmark),
    path('cocktail_by_ingredients', views.cocktails_by_ingredients, name='urlname'),
    path('cocktail_information', views.cocktail_by_information, name='urlname'),
    # path('personal_cocktail', views.personal_cocktail),
    # path('review', views.review, name='urlname'),
    path('user', views.user)
]
