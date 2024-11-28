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
from saleor.account.events import consecutive_login_balance_event, first_login_balance_event

from ....account.models import BalanceEvent, User
from ....order.utils import match_orders_with_new_user
from ....site.models import Site, SiteStatistics
from ...search import prepare_user_search_document_value


class Command(BaseCommand):
    help = "Used to mark poor students from a single JSON file."
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
        
        # 查询数据库里用户 jaccount 列表
        db_user_accounts = User.objects.values_list('account', flat=True)
        db_user_set = set(db_user_accounts)

        # 查询待导入的用户列表
        file_user_set = set([user["jaccount"] for user in users])

        # 构建差集
        inexistent_user_set = file_user_set - db_user_set
        if (len(inexistent_user_set) > 0):
            self.stdout.write(
                self.style.ERROR(
                    "Can not find %d poor students:\n%s"
                    % (len(inexistent_user_set), str(inexistent_user_set))
                )
            )
            return
        
        for userInfo in users:
            user_object = User.objects.get(
                account=userInfo.get("jaccount"),
            )
            user_object.private_metadata = user_object.private_metadata if user_object.private_metadata != None else {}
            user_object.private_metadata['is_poor'] = 'true'
            user_object.save(update_fields=["private_metadata", "search_document"])

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully marked %d poor students"
                % (len(file_user_set))
            )
        )
