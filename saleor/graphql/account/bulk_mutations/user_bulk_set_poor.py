import django
import graphene
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from ....account import models
from ....account.error_codes import AccountErrorCode
from ....order.actions import SiteStatistics
from ....permission.enums import AccountPermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_USERS
from ...core.mutations import BaseBulkMutation
from ...core.types import AccountError, NonNullList
from ..types import User


class UserBulkSetPoor(BaseBulkMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of user IDs to set as poor or not.",
        )
        is_poor = graphene.Boolean(
            required=True, description="Determine if users will be set as poor or not."
        )

    class Meta:
        description = "Set users as poor or not."
        doc_category = DOC_CATEGORY_USERS
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        if info.context.user == instance:
            raise ValidationError(
                {
                    "is_active": ValidationError(
                        "Cannot activate or deactivate your own account.",
                        code=AccountErrorCode.ACTIVATE_OWN_ACCOUNT.value,
                    )
                }
            )
        elif instance.is_superuser:
            raise ValidationError(
                {
                    "is_active": ValidationError(
                        "Cannot activate or deactivate superuser's account.",
                        code=AccountErrorCode.ACTIVATE_SUPERUSER_ACCOUNT.value,
                    )
                }
            )

    @classmethod
    def bulk_action(  # type: ignore[override]
        cls, _info: ResolveInfo, queryset, /, *, is_poor
    ):
        decrement = 0
        increment = 0
        with transaction.atomic():
            for user_object in queryset:
                user_object.private_metadata = user_object.private_metadata or {}
                user_object.private_metadata["is_poor"] = str(is_poor).lower()
                if is_poor and user_object.private_metadata.get("is_poor") != "true":
                    increment += 1
                elif (
                    not is_poor
                    and user_object.private_metadata.get("is_poor") == "true"
                ):
                    decrement += 1
                user_object.save(update_fields=["private_metadata", "search_document"])
            site, _ = Site.objects.get_or_create(id=settings.SITE_ID)
            try:
                stat = site.stat
            except:
                stat = SiteStatistics.objects.get_or_create(site=site)
            SiteStatistics.objects.filter(id=stat.id).update(
                poor_users=F("poor_users") + increment - decrement
            )
