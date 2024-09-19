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

from ....account.models import BalanceEvent, User
from ....order.utils import match_orders_with_new_user
from ....site.models import Site, SiteStatistics
from ...search import prepare_user_search_document_value


class Command(BaseCommand):
    help = "Used to import users from a single JSON file."
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
        file_user_set = set([user["userinfo"]["jaccount"] for user in users])

        # 构建差集
        do_import_user_set = file_user_set - db_user_set
        duplicate = len(file_user_set) - len(do_import_user_set)

        # 准备导入
        configuration = {
            item["name"]: item["value"]
            for item in settings.OPENID_PROVIDER_SETTINGS.get(settings.OPENID_PROVIDER)
        }
        oauth_url = configuration.get("oauth_authorization_url")
        oidc_metadata_key = f"oidc:{oauth_url}"
        
        log_number_dic = {}
        for user in users:
            userInfo = user["userinfo"]
            if (userInfo.get("jaccount") not in do_import_user_set):
                continue;
            defaults_create = {
                "is_active": True,
                "is_confirmed": True,
                "email": userInfo.get("email"),
                "account": userInfo.get("jaccount"),
                "user_type": "student",
                "first_name": userInfo.get("username"),
                "last_name": "",
                "code": "",
                "private_metadata": {oidc_metadata_key: userInfo.get("jaccount")},
                "password": make_password(None),
                "balance": Decimal(userInfo.get("coins")),
                "continuous": int(userInfo.get("continuous")),
                "last_login": datetime.datetime.strptime(
                    userInfo.get("last_login"), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=pytz.timezone("Asia/Shanghai")),
            }
            with transaction.atomic():
                user_object, _ = User.objects.get_or_create(
                    email=user.get("email"),
                    defaults=defaults_create,
                )
                user_object.search_document = prepare_user_search_document_value(
                    user_object, attach_addresses_data=False
                )
                user_object.save(update_fields=["search_document"])
                match_orders_with_new_user(user_object)
            coinlogs = user["coinlog"]
            bulk_data = []

            for log in coinlogs:
                num = log_number_dic.get(log.get("date")[:7], 0) + 1
                log_number_dic[log.get("date")[:7]] = num
                bulk_data.append(
                    BalanceEvent(
                        user=user_object,
                        type=log.get("type"),
                        balance=log.get("balance"),
                        delta=log.get("delta"),
                        date=datetime.datetime.strptime(
                            log.get("date"), "%Y-%m-%d %H:%M:%S"
                        ).replace(tzinfo=pytz.timezone("Asia/Shanghai")),
                        number=num
                    )
                )

            BalanceEvent.objects.bulk_create(
                bulk_data
            )

        site, _ = Site.objects.get_or_create(id=settings.SITE_ID)
        if not site.domain or not site.name:
            site.name = settings.SITE_NAME
            site.domain = settings.SITE_DOMAIN
            site.save(update_fields=["name", "domain"])
        try:
            stat = site.stat
        except:
            stat = SiteStatistics.objects.get_or_create(site=site)
        SiteStatistics.objects.filter(id=stat.id).update(users=F("users") + 1)
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully imported %d of %d accounts, %d skipped."
                % (len(do_import_user_set), len(file_user_set), duplicate)
            )
        )
