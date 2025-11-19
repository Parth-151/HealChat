from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from chatbot.models import AnalysisReport



def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('/chat/admin/')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
    if request.user.is_authenticated:
        return redirect('/chat/admin/')
    return render(request,'login.html')


@login_required
def logout_page(request):
    logout(request)  
    messages.success(request, 'You have been logged out successfully.') 
    return redirect('/')


def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if passwords match
        if password1 != confirm_password:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'signup.html')

        # Check if email is already taken
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use. Please try another.')
            return render(request, 'signup.html')

        # Create the new user
        user = User.objects.create_user(username=username, 
                                        email=email,
                                        password=password1
                                        )
        user.save()
        messages.success(request, 'Signup successful! You can now log in.')
        return redirect('login')
    if request.user.is_authenticated:
        return redirect('/chat/kishan/') #todo: pass usename
    return render(request, 'signup.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile, FriendRequest
from .forms import ProfileUpdateForm

@login_required
def profile(request, username):
    user_obj = get_object_or_404(User, username=username)
    profile = user_obj.profile

    # following/followers logic
    is_following = request.user.profile.friends.filter(id=profile.id).exists()
    follows_you = profile.friends.filter(id=request.user.profile.id).exists()

    # analysis
    last_report = AnalysisReport.objects.filter(user=user_obj).order_by("-timestamp").first()
    short_analysis = None

    if last_report:
        short_analysis = {
            "mood": last_report.mood_score,
            "stress": last_report.stress_level,
            "neg": last_report.negative_percentage,
        }

    from group.models import Group
    groups = Group.objects.filter(members=user_obj)

    return render(request, "users/profile.html", {
        "user_obj": user_obj,
        "profile": profile,
        "is_following": is_following,
        "follows_you": follows_you,
        "groups": groups,
        "short_analysis": short_analysis,
    })





@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("users:profile", username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def send_request(request, username):
    to_user = get_object_or_404(User, username=username)
    FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    return redirect("users:profile", username=username)

@login_required
def friends_list(request):
    friends = request.user.profile.friends.all()
    return render(request, "users/friends_list.html", {"friends": friends})


@login_required
def accept_request(request, id):
    req = get_object_or_404(FriendRequest, id=id)
    # Add friendship
    request.user.profile.friends.add(req.from_user.profile)
    req.from_user.profile.friends.add(request.user.profile)
    req.delete()
    return redirect("users:profile", username=request.user.username)

@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    request.user.profile.friends.add(user_to_follow.profile)
    return redirect("users:profile", username=username)


@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    request.user.profile.friends.remove(user_to_unfollow.profile)
    return redirect("users:profile", username=username)

@login_required
def choose_avatar(request):
    avatars = [
        "default1.png",
        "default2.png",
        "default3.png",
        "default4.png",
    ]

    if request.method == 'POST':
        filename = request.POST.get("avatar")
        request.user.profile.avatar = f"avatars/defaults/{filename}"
        request.user.profile.save()
        return redirect("users:profile", username=request.user.username)

    return render(request, "users/choose_avatar.html", {"avatars": avatars})
