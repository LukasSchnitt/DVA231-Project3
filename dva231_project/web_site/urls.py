from django.urls import path
from . import views


urlpatterns = [
    path('', views.home),
    path('user', views.user),
    path('bookmark', views.bookmark),
    path('test', views.test)
]
