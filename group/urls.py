from django.urls import path
from . import views

app_name = "group"

urlpatterns = [
    path("", views.group_list, name="group_list"),
    path("create/", views.group_create, name="group_create"),
    path("<slug:slug>/", views.group_chat, name="group_chat"),
    path("<slug:slug>/join/", views.join_group, name="join_group"),
    path("<slug:slug>/leave/", views.leave_group, name="leave_group"),
]
