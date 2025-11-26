from users.views import sidebar_context

def sidebar_data(request):
    if request.user.is_authenticated:
        return sidebar_context(request)
    return {}