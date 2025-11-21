from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, GroupMessage, DirectMessage
# Ensure you import both forms
from .forms import CreateGroupForm, GroupUpdateForm 
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse

User = get_user_model() # Define User globally for all views

@login_required
def search(request):
    q = request.GET.get("q", "").strip()
    users_data = []
    groups_data = []
    
    if q:
        users_qs = User.objects.filter(username__icontains=q).exclude(id=request.user.id)[:10]
        groups_qs = Group.objects.filter(name__icontains=q)[:10]
    else:
        users_qs = User.objects.none()
        groups_qs = Group.objects.none()

    for u in users_qs:
        avatar_url = "/static/avatars/defaults/default1.png"
        # Safety check
        if hasattr(u, 'profile'):
            avatar_url = u.profile.get_avatar_url() 

        users_data.append({
            "username": u.username,
            "avatar": avatar_url,
        })
            
    for g in groups_qs:
        groups_data.append({
            "name": g.name,
            "slug": g.slug,
        })

    return JsonResponse({"users": users_data, "groups": groups_data})


def sidebar_context(request):
    if not request.user.is_authenticated:
        return {}
    
    # 1. Groups
    groups_sidebar = Group.objects.filter(members=request.user).order_by("-created_at")
    
    # 2. Recent Direct Chats
    direct_msgs = DirectMessage.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by("-timestamp")
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
            recent_users.append(User.objects.get(id=uid))
            if len(recent_users) >= 10:
                break

    return {"groups_sidebar": groups_sidebar, "recent_users": recent_users}


# In group/views.py

@login_required
def chat_home(request):
    # Re-use the sidebar context so the sidebar appears
    context = sidebar_context(request)
    return render(request, "groups/chat_home.html", context)

@login_required
def group_list(request):
    context = sidebar_context(request)
    return render(request, "groups/group_list.html", context)


@login_required
def group_create(request):
    # Use context for sidebar
    context = sidebar_context(request)

    if request.method == "POST":
        form = CreateGroupForm(request.POST, request.FILES) # Added request.FILES for icon
        if form.is_valid():
            grp = form.save(commit=False)
            grp.created_by = request.user
            grp.save()
            grp.members.add(request.user)
            return redirect('group:group_chat', slug=grp.slug)
    else:
        form = CreateGroupForm()

    # Merge form into context
    context['form'] = form
    return render(request, "groups/group_create.html", context)


@login_required
def group_chat(request, slug):
    group = get_object_or_404(Group, slug=slug)
    is_member = group.members.filter(id=request.user.id).exists()

    if request.method == "POST" and is_member:
        content = request.POST.get("content", "").strip()
        if content:
            GroupMessage.objects.create(group=group, sender=request.user, content=content)
            return redirect('group:group_chat', slug=slug)

    # FIX 1: RENAME 'messages' to 'chat_messages'
    chat_messages = group.messages.select_related('sender').all()[:200]

    context = sidebar_context(request)
    context.update({
        "group": group,
        "chat_messages": chat_messages, # Use new name here
        "is_member": is_member
    })

    return render(request, "groups/group_chat.html", context)


@login_required
def join_group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group.members.add(request.user)
    return redirect('group:group_chat', slug=group.slug)


@login_required
def leave_group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group.members.remove(request.user)
    return redirect('group:chat_home')


@login_required
def direct_chat(request, username):
    other_user = get_object_or_404(User, username=username)

    # FIX 1: RENAME 'messages' to 'chat_messages'
    chat_messages = DirectMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("timestamp")

    # FIX 3: USE HELPER FUNCTION (Don't repeat logic)
    context = sidebar_context(request)
    
    context.update({
        "other_user": other_user,
        "chat_messages": chat_messages, # Use new name
    })

    return render(request, "chat/direct_chat.html", context)


@login_required
def group_profile(request, slug):
    group = get_object_or_404(Group, slug=slug)
    is_member = group.members.filter(id=request.user.id).exists()
    is_admin = (request.user == group.created_by)
    
    # Get Sidebar Data
    context = sidebar_context(request)

    if request.method == "POST" and is_admin:
        form = GroupUpdateForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            form.save()
            return redirect("group:group_profile", slug=group.slug)
    else:
        form = GroupUpdateForm(instance=group) if is_admin else None

    # FIX 2: MERGE DATA properly (don't nest it inside "context")
    context.update({
        "group": group,
        "is_member": is_member,
        "is_admin": is_admin,
        "form": form
    })

    return render(request, "groups/group_profile.html", context)