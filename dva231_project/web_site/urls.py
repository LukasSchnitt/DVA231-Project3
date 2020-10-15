from django.urls import path
from . import views


urlpatterns = [
    path('', views.home),
    path('user', views.user),
    path('bookmark', views.bookmark),
    path('review', views.review, name='urlname'),
    path('test', views.test)
]
