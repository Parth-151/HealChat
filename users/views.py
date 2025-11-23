# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q 
from .models import Profile
from .forms import ProfileUpdateForm
from chatbot.models import AnalysisReport
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# --- IMPORTS FROM GROUP APP ---
from group.models import Group, DirectMessage
import os

# ... (keep your existing imports) ...

# 1. Make sure you have this import if it's missing
from django.shortcuts import render

# 2. Add this NEW view function for Home
def home(request):
    context = {}
    # Only fetch sidebar data if logged in
    if request.user.is_authenticated:
        context = sidebar_context(request)
    
    return render(request, 'home.html', context)

# ---------------- Sidebar Context Helper ---------------- #
def sidebar_context(request):
    """
    Fetches Groups and Recent Chats for the Sidebar.
    """
    if not request.user.is_authenticated:
        return {}

    # 1. Fetch Groups
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

    seen = set()
    recent_users = []
    for uid in user_ids:
        if uid not in seen and uid != request.user.id:
            seen.add(uid)
            try:
                user = User.objects.get(id=uid)
                if not hasattr(user, 'profile'):
                    Profile.objects.create(user=user)
                recent_users.append(user)
            except User.DoesNotExist:
                continue
            
            if len(recent_users) >= 10:
                break
    
    return {
        "groups_sidebar": groups_sidebar, 
        "recent_users": recent_users
    }

# ---------------- Auth Views ---------------- #

def login_page(request):
    if request.user.is_authenticated:
        return redirect('group:chat_home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('group:chat_home')
        messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

@login_required
def logout_page(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('/')

def signup_view(request):
    # If already logged in, redirect
    if request.user.is_authenticated:
        return redirect('group:chat_home')

    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        pass1 = request.POST.get('password')
        pass2 = request.POST.get('confirm_password')

        # Validation 1: Empty Fields
        if not username or not email or not pass1:
            messages.error(request, "Please fill in all fields.")
            return render(request, 'users/signup.html')

        # Validation 2: Passwords Match
        if pass1 != pass2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'users/signup.html')

        # Validation 3: Uniqueness
        if User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
            return render(request, 'users/signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'users/signup.html')

        # Validation 4: Password Strength
        try:
            validate_password(pass1)
        except ValidationError as e:
            for err in e.messages:
                messages.error(request, err)
            return render(request, 'users/signup.html')

        # Creation
        try:
            user = User.objects.create_user(username=username, email=email, password=pass1)
            user.save()
            # Profile created by signals usually, but good to be safe
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)
            
            messages.success(request, "Account created! Please log in.")
            return redirect('users:login')
            
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return render(request, 'users/signup.html')

    return render(request, 'users/signup.html')

# ---------------- Profile Views ---------------- #

@login_required
def profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    if not hasattr(user_obj, 'profile'):
        Profile.objects.create(user=user_obj)
        
    profile_obj = user_obj.profile
    is_owner = (request.user == user_obj)

    # Get Stats
    last_report = AnalysisReport.objects.filter(user=user_obj).order_by('-timestamp').first()
    short_analysis = None
    if last_report:
        short_analysis = {
            "mood": last_report.mood_score,
            "stress": last_report.stress_level,
            "negative": last_report.negative_percentage,
        }

    # Groups for Profile Card
    groups = Group.objects.filter(members=user_obj)
    
    # --- SIDEBAR DATA ---
    context = sidebar_context(request)
    
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
            messages.success(request, "Profile updated!")
            return redirect("users:profile", username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=profile_obj)
    
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
            messages.success(request, "Avatar updated!")
            return redirect("users:profile", username=request.user.username)

    context = sidebar_context(request)
    context['avatars'] = avatars
    return render(request, "users/choose_avatar.html", context)

# users/views.py
from .models import Feedback # Import the model

@login_required
def feedback_view(request):
    # 1. Sidebar Context (So sidebar doesn't disappear)
    context = sidebar_context(request)
    
    if request.method == "POST":
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        rating = request.POST.get('rating')
        
        # Save to DB
        Feedback.objects.create(
            user=request.user,
            subject=subject,
            message=message,
            rating=rating
        )
        
        messages.success(request, "Thank you! Your feedback has been recorded.")
        return redirect('home') # Redirects to home after submitting

    return render(request, 'users/feedback.html', context)