import graphene
from django.utils import timezone

from saleor.graphql.core import ResolveInfo

from ....account import BalanceEvents
from ....account import models as account_models
from ....donation import DonationStatus
from ....donation import models as donation_models
from ....permission.enums import DonationPermissions
from ...core.doc_category import DOC_CATEGORY_DONATIONS
from ...core.mutations import BaseBulkMutation
from ...core.types.common import DonationBulkError, NonNullList
from django.db.models.manager import BaseManager
from ..types import Donation

class DonationBulkComplete(BaseBulkMutation):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were updated.",
    )

    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of donations to be updated."
        )
        accepted = graphene.Boolean(
            required=True,
        )
    class Meta:
        description = "Complete donations"
        doc_category = DOC_CATEGORY_DONATIONS
        model = donation_models.Donation
        object_type = Donation
        permissions = (DonationPermissions.MANAGE_DONATIONS,)
        error_type_class = DonationBulkError
        error_type_field = "donation_errors"

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset: BaseManager[Donation], accepted: bool, **data):
        donations = list(queryset)
        updates = []
        updated_users = []
        events = []
        for donation in donations:
            donation.updated_at = timezone.now()
            if (
                donation.status != DonationStatus.COMPLETED
                and accepted
                and donation.donator
            ):
                try:
                    user = account_models.User.objects.get(code=donation.donator)
                    user.balance += donation.price_amount or 0
                    updated_users.append(user)
                    events.append(
                        account_models.BalanceEvent(
                            user=user,
                            type=BalanceEvents.DONATION_GRANTED,
                            balance=user.balance,
                            delta=(donation.price_amount or 0),
                        )
                    )
                except (
                    account_models.User.DoesNotExist,
                    account_models.User.MultipleObjectsReturned,
                ):
                    pass
            elif (
                donation.status == DonationStatus.COMPLETED
                and not accepted
                and donation.donator
            ):
                try:
                    user = account_models.User.objects.get(code=donation.donator)
                    user.balance -= donation.price_amount or 0
                    updated_users.append(user)
                    events.append(
                        account_models.BalanceEvent(
                            user=user,
                            type=BalanceEvents.DONATION_REJECTED,
                            balance=user.balance,
                            delta=-(donation.price_amount or 0),
                        )
                    )
                except (
                    account_models.User.DoesNotExist,
                    account_models.User.MultipleObjectsReturned,
                ):
                    pass

            if accepted:
                donation.status = DonationStatus.COMPLETED
            else:
                donation.status = DonationStatus.REJECTED

            updates.append(donation)

        donation_models.Donation.objects.bulk_update(
            donations,
            fields=[
                "status",
                "updated_at",
            ],
        )
        account_models.User.objects.bulk_update(updated_users, fields=["balance"])
        account_models.BalanceEvent.objects.bulk_create(events)
        return DonationBulkComplete(count=len(updates))