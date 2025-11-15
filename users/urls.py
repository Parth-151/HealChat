
from django.urls import path
from users.views import login_page, logout_page, signup_view

urlpatterns = [
    path('', login_page, name="login"),
    path('logout/', logout_page, name="logout"),
    path('signup/', signup_view, name="signup"),
]
