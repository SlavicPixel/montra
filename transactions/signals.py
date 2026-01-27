from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transaction
from .services.dashboard_cache import bump_dash_version

@receiver(post_save, sender=Transaction)
def txn_saved(sender, instance: Transaction, **kwargs):
    bump_dash_version(instance.user_id)

@receiver(post_delete, sender=Transaction)
def txn_deleted(sender, instance: Transaction, **kwargs):
    bump_dash_version(instance.user_id)
