from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q 
from .models import Profile
from .forms import ProfileUpdateForm
from chatbot.models import AnalysisReport

# --- IMPORTS FROM GROUP APP (Crucial for Sidebar) ---
from group.models import Group, DirectMessage
import os

# ---------------- Sidebar Context Helper ---------------- #
def sidebar_context(request):
    """
    Fetches Groups and Recent Chats for the Sidebar.
    Used by Profile, Edit Profile, and Avatar pages.
    """
    if not request.user.is_authenticated:
        return {}

    # 1. Fetch Groups (Logged-in user is a member)
    groups_sidebar = Group.objects.filter(members=request.user).order_by("-created_at")

    # 2. Fetch Recent Direct Chats
    direct_msgs = DirectMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by("-timestamp").select_related('sender', 'receiver')

    user_ids = []
    for dm in direct_msgs:
        if dm.sender_id != request.user.id:
            user_ids.append(dm.sender_id)
        if dm.receiver_id != request.user.id:
            user_ids.append(dm.receiver_id)

    # Filter unique users while preserving order (Most recent first)
    seen = set()
    recent_users = []
    for uid in user_ids:
        if uid not in seen and uid != request.user.id:
            seen.add(uid)
            try:
                user = User.objects.get(id=uid)
                # Ensure profile exists to prevent template crash
                if not hasattr(user, 'profile'):
                    Profile.objects.create(user=user)
                recent_users.append(user)
            except User.DoesNotExist:
                continue
            
            if len(recent_users) >= 10: # Limit to 10
                break
    
    # DEBUG: Print to terminal to verify it works
    print(f"Sidebar Loaded for {request.user}: {len(groups_sidebar)} Groups, {len(recent_users)} Chats")

    return {
        "groups_sidebar": groups_sidebar, 
        "recent_users": recent_users
    }

# ---------------- Auth Views ---------------- #
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('group:chat_home') # Redirect to Chat Home
        messages.error(request, 'Invalid username or password.')
    
    if request.user.is_authenticated:
        return redirect('group:chat_home')
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

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'signup.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        # Create Profile immediately
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)
            
        messages.success(request, 'Signup successful! Please login.')
        return redirect('users:login')
        
    if request.user.is_authenticated:
        return redirect('group:chat_home')
    return render(request, 'signup.html')

# ---------------- Profile Views ---------------- #

@login_required
def profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    
    # Ensure profile exists
    if not hasattr(user_obj, 'profile'):
        Profile.objects.create(user=user_obj)
        
    profile_obj = user_obj.profile
    is_owner = (request.user == user_obj)

    # Analysis Report
    last_report = AnalysisReport.objects.filter(user=user_obj).order_by('-timestamp').first()
    short_analysis = None
    if last_report:
        short_analysis = {
            "mood": last_report.mood_score,
            "stress": last_report.stress_level,
            "negative": last_report.negative_percentage,
        }

    # Groups for the Profile Card (NOT the sidebar)
    groups = Group.objects.filter(members=user_obj)
    
    # --- KEY FIX: Get Sidebar Data ---
    context = sidebar_context(request)
    
    # Merge data
    context.update({
        "user_obj": user_obj,
        "profile": profile_obj,
        "is_owner": is_owner,
        "short_analysis": short_analysis,
        "groups": groups, 
    })

    return render(request, "users/profile.html", context)

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
    
    # --- KEY FIX: Get Sidebar Data ---
    context = sidebar_context(request)
    context['form'] = form
    
    return render(request, "users/edit_profile.html", context)

@login_required
def choose_avatar(request):
    defaults_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "avatars", "defaults")
    try:
        avatars = [f for f in os.listdir(defaults_dir) if f.lower().endswith((".png",".jpg",".jpeg",".webp"))]
    except FileNotFoundError:
        avatars = []

    if request.method == "POST":
        selected = request.POST.get("avatar")
        if selected in avatars:
            profile = request.user.profile
            profile.preset_avatar = selected
            profile.avatar = None 
            profile.save()
            messages.success(request, "Avatar updated successfully!")
            return redirect("users:profile", username=request.user.username)

    # --- KEY FIX: Get Sidebar Data ---
    context = sidebar_context(request)
    context['avatars'] = avatars
    
    return render(request, "users/choose_avatar.html", context)