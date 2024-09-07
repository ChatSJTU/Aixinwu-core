
from django.core.management.base import BaseCommand

from ....account.models import User


class Command(BaseCommand):
    help = "Delete all users except staff"

    def handle(self, *args, **options):
        try:
            u = User.objects.filter(is_staff=False)

            deleted_count, _ = u.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    "Deleted %d users"
                    % deleted_count
                )
            )
        except Exception as ex:
            self.stdout.write(
                self.style.WARNING(
                    ex.__str__()
                )
            )
