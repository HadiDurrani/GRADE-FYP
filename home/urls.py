from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='home'),  # Root URL for the home app
    path('learnmore/', views.learnmore, name='learnmore'), #learn more page
    path('login/', views.login, name= 'login'),
    path("sandbox/", views.sandbox, name="sandbox")
]
