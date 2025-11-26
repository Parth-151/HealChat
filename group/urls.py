from django.urls import path
from . import views

app_name = "group"

urlpatterns = [
    path("", views.chat_home, name="chat_home"),

    path("search/", views.search, name="search"),
    path("create/", views.group_create, name="group_create"),
    path("<slug:slug>/info/", views.group_profile, name="group_profile"),
    path("<slug:slug>/join/", views.join_group, name="join_group"),
    path("<slug:slug>/leave/", views.leave_group, name="leave_group"),
    path("<slug:slug>/", views.group_chat, name="group_chat"),
    path("chat/<slug:username>/", views.direct_chat, name="direct_chat"),
    path('<slug:slug>/remove/<int:user_id>/', views.remove_member, name='remove_member'),
]
