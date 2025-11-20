from django.urls import path
from users.views import login_page, logout_page, signup_view
from . import views

app_name = 'users'

urlpatterns = [
    path('login', login_page, name="login"),
    path('logout/', logout_page, name="logout"),
    path('signup/', signup_view, name="signup"),

    # Profile
    path('profile/<str:username>/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('choose-avatar/', views.choose_avatar, name='choose_avatar'),
]
