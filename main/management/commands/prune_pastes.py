from django.core.management.base import BaseCommand
from django.utils import timezone

from main.models import Paste


class Command(BaseCommand):
    help = "Delete all expired pastes."

    def handle(self, *args, **options):
        pastes = Paste.objects.filter(expiration__lt=timezone.now()).exclude(
            expiration__isnull=True
        )
        print("Deleting %s pastes..." % pastes.count())
        pastes.delete()
        print("Done.")
