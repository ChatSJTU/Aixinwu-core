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
    help = "Used to import poor students from a single JSON file."
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
        new_user_set = file_user_set - db_user_set
        duplicate_count = len(file_user_set) - len(new_user_set)

        # 准备导入
        configuration = {
            item["name"]: item["value"]
            for item in settings.OPENID_PROVIDER_SETTINGS.get(settings.OPENID_PROVIDER)
        }
        oauth_url = configuration.get("oauth_authorization_url")
        oidc_metadata_key = f"oidc:{oauth_url}"
        
        for userInfo in users:
            if (userInfo.get("jaccount") not in new_user_set): # 已存在
                user_object = User.objects.get(
                    email=userInfo.get("email"),
                )
            else:
                defaults_create = {
                    "is_active": True,
                    "is_confirmed": True,
                    "email": userInfo.get("email"),
                    "account": userInfo.get("jaccount"),
                    "user_type": "student",
                    "first_name": userInfo.get("username"),
                    "last_name": "",
                    "code": userInfo.get("code"),
                    "private_metadata": {oidc_metadata_key: userInfo.get("jaccount")},
                    "password": make_password(None),
                    "balance": Decimal(0),
                    "continuous": 0,
                    "last_login": datetime.datetime(1970, 1, 1, tzinfo=pytz.timezone("Asia/Shanghai")),
                }
                with transaction.atomic():
                    user_object, _ = User.objects.get_or_create(
                        email=userInfo.get("email"),
                        defaults=defaults_create,
                    )
                    user_object.search_document = prepare_user_search_document_value(
                        user_object, attach_addresses_data=False
                    )
                    user_object.save(update_fields=["search_document"])
                    match_orders_with_new_user(user_object)
                
                # first_login_balance_event(user=user_object)
                # consecutive_login_balance_event(
                #     user=user_object, delta=Decimal(settings.CONTINUOUS_BALANCE_ADD[0])
                # )
            user_object.balance += 800            
            user_object.private_metadata['is_poor'] = 'true'
            user_object.save(update_fields=['balance', "private_metadata", "search_document"])
            BalanceEvent.objects.create(
                user=user_object,
                type=BalanceEvents.POOR_SIGN,
                balance=user_object.balance,
                delta=800,
            )

        site, _ = Site.objects.get_or_create(id=settings.SITE_ID)
        try:
            stat = site.stat
        except:
            stat = SiteStatistics.objects.get_or_create(site=site)
        SiteStatistics.objects.filter(id=stat.id).update(users=F("users") + len(new_user_set))
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully imported %d poor students (%d new user added, %d existing user updated)."
                % (len(file_user_set), len(new_user_set), duplicate_count)
            )
        )
