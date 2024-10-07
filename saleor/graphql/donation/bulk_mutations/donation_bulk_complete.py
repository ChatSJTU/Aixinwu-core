import graphene
from django.db.models import Q
from django.utils import timezone

from ....account import BalanceEvents
from ....account import models as account_models
from ....donation import DonationStatus
from ....donation import models as donation_models
from ....donation.error_codes import DonationErrorCode
from ....permission.enums import DonationPermissions
from ...core.doc_category import DOC_CATEGORY_DONATIONS
from ...core.mutations import BaseMutation
from ...core.types.base import BaseInputObjectType, BaseObjectType
from ...core.types.common import DonationBulkError, NonNullList
from ..mutations.donation_update import DonationUpdate, DonationUpdateInput
from ..types import Donation


class DonationBulkCompleteInput(BaseInputObjectType):
    id = graphene.ID(required=True, description="ID of the donation.")
    accepted = graphene.Boolean(
        required=True,
    )


class DonationBulkCompleteResult(BaseObjectType):
    donation = graphene.Field(
        Donation, required=False, description="The updated donation"
    )
    errors = NonNullList(
        DonationBulkError, required=False, description="The updated errors."
    )


class DonationBulkComplete(BaseMutation):
    donations = NonNullList(
        Donation, required=True, description="Input list of donations"
    )
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were updated.",
    )

    class Arguments:
        donations = NonNullList(
            DonationBulkCompleteInput,
            required=True,
            description="Input list of donations to be updated",
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
    def get_donations(cls, donations):
        if not donations:
            return list()
        filter = Q()
        for donation in donations:
            filter |= Q(pk=donation.id)
        return {
            str(donation.id): donation
            for donation in donation_models.Donation.objects.filter(filter).iterator()
        }

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        donations: list = data.get("donations")
        for donation in donations:
            donation.id = cls.get_global_id_or_error(donation.id)
        instances_map = cls.get_donations(donations)
        results = []
        updates = []
        updated_users = []
        events = []
        for donation in donations:
            if instance := instances_map.get(donation.id):
                instance.updated_at = timezone.now()
                if (
                    instance.status != DonationStatus.COMPLETED
                    and donation.accepted
                    and instance.donator
                ):
                    try:
                        user = account_models.User.objects.get(code=instance.donator)
                        user.balance += instance.price_amount or 0
                        updated_users.append(user)
                        events.append(
                            account_models.BalanceEvent(
                                user=user,
                                type=BalanceEvents.DONATION_GRANTED,
                                balance=user.balance,
                                delta=(instance.price_amount or 0),
                            )
                        )
                    except (
                        account_models.User.DoesNotExist,
                        account_models.User.MultipleObjectsReturned,
                    ):
                        pass
                elif (
                    instance.status == DonationStatus.COMPLETED
                    and not donation.accepted
                    and instance.donator
                ):
                    try:
                        user = account_models.User.objects.get(code=instance.donator)
                        user.balance -= instance.price_amount or 0
                        updated_users.append(user)
                        events.append(
                            account_models.BalanceEvent(
                                user=user,
                                type=BalanceEvents.DONATION_REJECTED,
                                balance=user.balance,
                                delta=-(instance.price_amount or 0),
                            )
                        )
                    except (
                        account_models.User.DoesNotExist,
                        account_models.User.MultipleObjectsReturned,
                    ):
                        pass

                if donation.accepted:
                    instance.status = DonationStatus.COMPLETED
                else:
                    instance.status = DonationStatus.REJECTED

                updates.append(instance)
                results.append(DonationBulkCompleteResult(donation=donation, errors=[]))
            else:
                results.append(DonationBulkCompleteResult(donation=None, errors=[]))

        donation_models.Donation.objects.bulk_update(
            updates,
            fields=[
                "status",
            ],
        )
        account_models.User.objects.bulk_update(updated_users, fields=["balance"])
        account_models.BalanceEvent.objects.bulk_create(events)
        return DonationBulkComplete(count=len(updates), donations=updates)
