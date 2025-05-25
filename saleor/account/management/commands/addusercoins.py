import datetime
import json
from decimal import Decimal

import pytz
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F

from saleor.account import BalanceEvents
from saleor.account.events import change_balance_event, consecutive_login_balance_event, first_login_balance_event

from ....account.models import BalanceEvent, User
from ....order.utils import match_orders_with_new_user
from ....site.models import Site, SiteStatistics
from ...search import prepare_user_search_document_value


class Command(BaseCommand):
    help = "Used to increase user coins from a single JSON file."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument("json_file", nargs=1, type=str)

    def handle(self, *args, **options):
        file = options["json_file"][0]
        try:
            users = json.load(open(file))
        except OSError:
            raise CommandError("Failed to open file %s" % file)
        except json.JSONDecodeError:
            raise CommandError("%s does not seem to be a valid JSON file." % file)

        updated_count = 0
        for userInfo in users:
            try:
                user_object = User.objects.get(
                    code=userInfo.get("code"),
                )
            except:
                try:
                    user_object = User.objects.get(
                        email=userInfo.get("email"),
                    )
                except:
                    print(f"user with code {userInfo.get('code')} and email {userInfo.get('email')} not exists!")
                    continue
            with transaction.atomic():
                updated_balance = user_object.balance + Decimal(userInfo.get('bonus'))
                change_balance_event(user=user_object, balance=updated_balance, type=BalanceEvents.BONUS)
                user_object.balance = updated_balance
                user_object.save(update_fields=["balance"])
                updated_count = updated_count + 1
                

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully updated %d students."
                % (updated_count)
            )
        )
