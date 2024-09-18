
from django.core.management.base import BaseCommand

from saleor.donation.models import Donation


class Command(BaseCommand):
    help = "Delete all donations"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        try:
            u = Donation.objects.all()

            deleted_count, _ = u.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    "Deleted %d donations"
                    % deleted_count
                )
            )
        except Exception as ex:
            self.stdout.write(
                self.style.WARNING(
                    ex.__str__()
                )
            )
