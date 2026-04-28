"""
SkillTree AI - Study Group Signals
Signal handlers for broadcasting skill completion to group chat.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from skills.models import SkillProgress
from users.models import StudyGroupMembership


@receiver(post_save, sender=SkillProgress)
def broadcast_skill_completion(sender, instance, created, **kwargs):
    """
    Broadcast skill completion to all group members' chat channels.
    """
    if instance.status != 'completed':
        return

    user = instance.user
    skill = instance.skill

    memberships = StudyGroupMembership.objects.filter(user=user)

    channel_layer = get_channel_layer()

    for membership in memberships:
        group_name = f'group_{membership.group.id}'

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'skill_completed',
                'user_id': user.id,
                'username': user.username,
                'skill_title': skill.title,
            }
        )
