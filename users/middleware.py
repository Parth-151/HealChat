from django.utils import timezone
from django.conf import settings

class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        response = self.get_response(request)
        try:
            if request.user.is_authenticated:
                profile = request.user.profile
                profile.last_seen = timezone.now()
                profile.save(update_fields=["last_seen"])
        except Exception:
            pass
        return response
