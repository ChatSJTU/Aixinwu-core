import datetime
import json
from decimal import Decimal

import pytz
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError

from ....account.models import User
from ....order.utils import match_orders_with_new_user
from ....site.models import Site, SiteStatistics


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
        configuration = {
            item["name"]: item["value"]
            for item in settings.OPENID_PROVIDER_SETTINGS.get(settings.OPENID_PROVIDER)
        }
        oauth_url = configuration.get("oauth_authorization_url")
        oidc_metadata_key = f"oidc:{oauth_url}"
        duplicate = 0
        for user in users:
            get_kwargs = {
                "private_metadata__contains": {oidc_metadata_key: user.get("jaccount")}
            }
            try:
                user_object = User.objects.using(
                    settings.DATABASE_CONNECTION_REPLICA_NAME
                ).get(**get_kwargs)
                self.stdout.write(
                    self.style.WARNING(
                        "User with jaccount %s already exists, skipping."
                        % user.get("jaccount")
                    )
                )
                duplicate += 1
            except User.DoesNotExist:
                defaults_create = {
                    "is_active": True,
                    "is_confirmed": True,
                    "email": user.get("email"),
                    "account": user.get("jaccount"),
                    "user_type": "student",
                    "first_name": user.get("username"),
                    "last_name": "",
                    "code": "",
                    "private_metadata": {oidc_metadata_key: user.get("jaccount")},
                    "password": make_password(None),
                    "balance": Decimal(user.get("coins")),
                    "continuous": int(user.get("continuous")),
                    "last_login": datetime.datetime.strptime(
                        user.get("last_login"), "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=pytz.timezone("Asia/Shanghai")),
                }
                user_object, _ = User.objects.get_or_create(
                    email=user.get("email"),
                    defaults=defaults_create,
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
                stat.users += 1
                stat.save(update_fields=["users"])
                match_orders_with_new_user(user_object)
        self.stdout.write(
            self.style.SUCCESS(
                "Successfully imported %d of %d accounts, %d skipped."
                % (len(users) - duplicate, len(users), duplicate)
            )
        )
