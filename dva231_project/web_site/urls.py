from . import views
from django.urls import path


urlpatterns = [
    path('', views.home),
    path('profile', views.profile),
    path('bookmark', views.bookmark),
    path('cocktail', views.cocktail_API, name='urlname'),
    path('notifications', views.notifications),
    path('review', views.review, name='urlname'),
    path('user', views.user, name='urlname'),
    path('test', views.test)
]
