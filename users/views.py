from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Profile
from .forms import ProfileUpdateForm
from chatbot.models import AnalysisReport
from group.models import Group
import os, random

# ---------------- Sidebar Context ---------------- #
def sidebar_context(request):
    if not request.user.is_authenticated:
        return {}
    all_users = User.objects.exclude(id=request.user.id)
    random_people = random.sample(list(all_users), min(5, len(all_users))) if all_users else []
    return {"random_people": random_people}

# ---------------- Login / Logout / Signup ---------------- #
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('users:profile', username=user.username)
        messages.error(request, 'Invalid username or password.')
    if request.user.is_authenticated:
        return redirect('/chat/admin/')
    return render(request, 'login.html')

@login_required
def logout_page(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('/')

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password1 != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already in use.')
            return render(request, 'signup.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        messages.success(request, 'Signup successful!')
        return redirect('users:login')
    if request.user.is_authenticated:
        return redirect(f'/chat/{request.user.username}/')
    return render(request, 'signup.html')

# ---------------- Profile ---------------- #
@login_required
def profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    profile_obj = user_obj.profile
    is_owner = (request.user == user_obj)

    last_report = AnalysisReport.objects.filter(user=user_obj).order_by('-timestamp').first()
    short_analysis = None
    if last_report:
        short_analysis = {
            "mood": last_report.mood_score,
            "stress": last_report.stress_level,
            "negative": last_report.negative_percentage,
        }

    groups = Group.objects.filter(members=user_obj)
    base_context = sidebar_context(request)

    return render(request, "users/profile.html", {
        "user_obj": user_obj,
        "profile": profile_obj,
        "is_owner": is_owner,
        "short_analysis": short_analysis,
        "groups": groups,
        **base_context
    })

@login_required
def edit_profile(request):
    profile_obj = request.user.profile
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("users:profile", username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=profile_obj)
    return render(request, "users/edit_profile.html", {"form": form})

@login_required
def choose_avatar(request):
    defaults_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "avatars", "defaults")
    avatars = [f for f in os.listdir(defaults_dir) if f.lower().endswith((".png",".jpg",".jpeg",".webp"))]

    if request.method == "POST":
        selected = request.POST.get("avatar")
        if selected in avatars:
            profile = request.user.profile
            profile.preset_avatar = selected
            profile.avatar = None
            profile.save()
            messages.success(request, "Avatar updated successfully!")
            return redirect("users:profile", username=request.user.username)

    return render(request, "users/choose_avatar.html", {"avatars": avatars})
