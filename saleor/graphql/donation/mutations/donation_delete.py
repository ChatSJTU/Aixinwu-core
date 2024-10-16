import datetime
import graphene
import pytz

from saleor.graphql.donation.resolvers import resolve_donation_by_id

from ...core.mutations import ModelMutation
from ...core.doc_category import DOC_CATEGORY_DONATIONS
from ..types import Donation
from ....donation import models
from ...core.types.common import DonationError
from ....webhook.event_types import WebhookEventAsyncType
from ...core.utils import WebhookEventInfo
from ....permission.enums import DonationPermissions


class DonationDelete(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True)

    class Meta:
        description = "Delete an old donation."
        doc_category = DOC_CATEGORY_DONATIONS
        model = models.Donation
        object_type = graphene.Boolean
        return_field_name = "success"
        error_type_class = DonationError
        error_type_fields = "donation_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.DONATION_DELETED,
                description="A donation has been deleted.",
            )
        ]

    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        # donation = resolve_donation_by_id(info, data["id"])
        # if (
        #     donation.donator.id != info.context.user.id
        #     or not info.context.user.has_perm(DonationPermissions.MANAGE_DONATIONS)
        # ):
        #     return cls(errors=[DonationError(code="PERMISSION_DENIED")], success=False)
        # donation.deleted_at = pytz.utc.localize(datetime.datetime.now())
        # donation.updated_at = pytz.utc.localize(datetime.datetime.now())
        # donation.save(update_fields=["deleted_at", "updated_at"])
        return cls(errors=[], success=False)
