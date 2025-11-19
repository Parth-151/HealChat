
from django.urls import path
from users.views import login_page, logout_page, signup_view
from . import views

app_name = 'users'

urlpatterns = [
    path('login', login_page, name="login"),
    path('logout/', logout_page, name="logout"),
    path('signup/', signup_view, name="signup"),
    path("profile/<str:username>/", views.profile, name="profile"),
    path("edit/", views.edit_profile, name="edit_profile"),
    path("send/<str:username>/", views.send_request, name="send_request"),
    path("accept/<int:id>/", views.accept_request, name="accept_request"),
]

