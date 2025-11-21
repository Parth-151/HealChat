from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, GroupMessage, DirectMessage
from .forms import CreateGroupForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q

from django.http import JsonResponse

@login_required
def search(request):
    q = request.GET.get("q", "").strip()
    users_data = []
    groups_data = []
    print("q:",q)
    
    if q:
        # 'icontains' handles partial search (e.g., 'ra' finds 'Rahul' and 'Kiran')
        users_qs = User.objects.filter(username__icontains=q).exclude(id=request.user.id)[:10]
        groups_qs = Group.objects.filter(name__icontains=q)[:10]
        print("User:",users_qs)
    else:
        users_qs = User.objects.none()
        groups_qs = Group.objects.none()

    for u in users_qs:
        # SAFETY CHECK: Ensure profile exists to prevent crash
        avatar_url = "/static/avatars/defaults/default1.png"
        if hasattr(u, 'profile'):
            # FIX IS HERE: Added () to call the method
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
    # groups user belongs
    groups_sidebar = Group.objects.filter(members=request.user).order_by("-created_at")
    # recent direct chat users
    direct_msgs = DirectMessage.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by("-timestamp")
    user_ids = []
    for dm in direct_msgs:
        if dm.sender_id != request.user.id:
            user_ids.append(dm.sender_id)
        if dm.receiver_id != request.user.id:
            user_ids.append(dm.receiver_id)
    # unique and preserve order
    seen = set()
    recent_users = []
    for uid in user_ids:
        if uid not in seen and uid != request.user.id:
            seen.add(uid)
            recent_users.append(User.objects.get(id=uid))
            if len(recent_users) >= 10:
                break

    return {"groups_sidebar": groups_sidebar, "recent_users": recent_users}


@login_required
def group_list(request):
    context = sidebar_context(request)
    return render(request, "groups/group_list.html", context)



@login_required
def group_create(request):
    groups, recent_users = sidebar_context(request)

    if request.method == "POST":
        form = CreateGroupForm(request.POST)
        if form.is_valid():
            grp = form.save(commit=False)
            grp.created_by = request.user
            grp.save()
            grp.members.add(request.user)
            return redirect('group:group_chat', slug=grp.slug)
    else:
        form = CreateGroupForm()

    return render(request, "groups/group_create.html", {
        "form": form,
        "groups": groups,
        "recent_users": recent_users
    })
@login_required
def group_chat(request, slug):

    group = get_object_or_404(Group, slug=slug)
    is_member = group.members.filter(id=request.user.id).exists()

    if request.method == "POST" and is_member:
        content = request.POST.get("content", "").strip()
        if content:
            GroupMessage.objects.create(group=group, sender=request.user, content=content)
            return redirect('group:group_chat', slug=slug)

    messages = group.messages.select_related('sender').all()[:200]

    context = sidebar_context(request)
    context.update({
        "group": group,
        "messages": messages,
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
    return redirect('group:group_list')

User = get_user_model()
@login_required
def direct_chat(request, username):
    from django.contrib.auth.models import User
    from .models import Group, DirectMessage

    other_user = get_object_or_404(User, username=username)

    # Fetch chat messages
    messages = DirectMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("timestamp")

    # Sidebar context (IMPORTANT)
    groups_sidebar = Group.objects.filter(members=request.user)

    # Recent direct chat users
    recent_users = User.objects.filter(
        Q(sent_messages__receiver=request.user) |
        Q(received_messages__sender=request.user)
    ).exclude(id=request.user.id).distinct()

    return render(request, "chat/direct_chat.html", {
        "other_user": other_user,
        "messages": messages,
        "groups_sidebar": groups_sidebar,
        "recent_users": recent_users,
    })

