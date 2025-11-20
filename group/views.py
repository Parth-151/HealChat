from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, GroupMessage, DirectMessage
from .forms import CreateGroupForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q

def sidebar_data(request):
    # Groups user is a member of
    groups = Group.objects.filter(members=request.user)
    print(groups)

    # Users recently chatted (direct messages)
    direct_ids = DirectMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).values_list("sender", "receiver")

    user_ids = set()
    for s, r in direct_ids:
        if s != request.user.id:
            user_ids.add(s)
        if r != request.user.id:
            user_ids.add(r)

    recent_users = User.objects.filter(id__in=user_ids)

    return groups, recent_users


@login_required
def group_list(request):
    groups, recent_users = sidebar_data(request)
    return render(request, "groups/group_list.html", {
        "groups": groups,
        "recent_users": recent_users
    })


@login_required
def group_create(request):
    groups, recent_users = sidebar_data(request)

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
    groups, recent_users = sidebar_data(request)

    group = get_object_or_404(Group, slug=slug)
    is_member = group.members.filter(id=request.user.id).exists()

    messages = group.messages.select_related('sender').all().order_by('timestamp')[:200]

    return render(request, "groups/group_chat.html", {
        "group": group,
        "messages": messages,
        "is_member": is_member,
        "groups_sidebar": groups,
        "recent_users": recent_users
    })


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
def direct_chat(request, slug):
    groups, recent_users = sidebar_data(request)

    other_user = get_object_or_404(User, username=slug)

    messages = DirectMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("timestamp")

    return render(request, "chat/direct_chat.html", {
        "other_user": other_user,
        "messages": messages,
        "groups_sidebar": groups,
        "recent_users": recent_users
    })


