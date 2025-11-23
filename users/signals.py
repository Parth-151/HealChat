from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from group.models import Group

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    try:
            # Try to find a group named 'Community' or create it if it doesn't exist
            community_group, _ = Group.objects.get_or_create(
                slug='community', 
                defaults={
                    'name': 'Community', 
                    'description': 'The official safe space for everyone.',
                    'created_by': instance # The first user becomes admin, or set specific ID
                }
            )
            community_group.members.add(instance)
    except Exception as e:
            print(f"Auto-join error: {e}")