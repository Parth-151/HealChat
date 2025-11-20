from django.contrib.auth.models import User

def sidebar_data(request):
    if not request.user.is_authenticated:
        return {}

    # friends = request.user.profile.friends.all()

    random_people = User.objects.exclude(id=request.user.id).order_by('?')[:5]

    return {
        # "friends": friends,
        "random_people": random_people
    }
