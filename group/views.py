from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, GroupMessage, DirectMessage
from .forms import CreateGroupForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q

@login_required
def group_list(request):
    groups = Group.objects.all().order_by('-created_at')
    return render(request, "groups/group_list.html", {"groups": groups})

@login_required
def group_create(request):
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
    return render(request, "groups/group_create.html", {"form": form})

@login_required
def group_chat(request, slug):
    group = get_object_or_404(Group, slug=slug)
    is_member = group.members.filter(id=request.user.id).exists()
    messages = group.messages.select_related('sender').all().order_by('timestamp')[:200]
    return render(request, "groups/group_chat.html", {
        "group": group,
        "messages": messages,
        "is_member": is_member,
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
    other_user = get_object_or_404(User, username=slug)

    messages = DirectMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("timestamp")
    print(messages)

    return render(request, "chat/direct_chat.html", {
        "other_user": other_user,
        "messages": messages
    })

