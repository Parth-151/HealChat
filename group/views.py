from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, GroupMessage
from .forms import CreateGroupForm

def group_list(request):
    groups = Group.objects.all().order_by('-created_at')
    return render(request, "group_list.html", {"groups": groups})

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
    return render(request, "group_create.html", {"form": form})

def group_chat(request, slug):
    group = get_object_or_404(Group, slug=slug)
    is_member = group.members.filter(id=request.user.id).exists()
    messages = group.messages.select_related('sender').all().order_by('timestamp')[:200]
    return render(request, "group_chat.html", {
        "group": group,
        "messages": messages,
        "is_member": is_member,
    })

def join_group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group.members.add(request.user)
    return redirect('group:group_chat', slug=group.slug)

def leave_group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group.members.remove(request.user)
    return redirect('group:group_list')
