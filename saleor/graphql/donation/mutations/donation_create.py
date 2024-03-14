from ...core import ResolveInfo
from ...core.utils import WebhookEventInfo
from ....webhook.event_types import WebhookEventAsyncType
from ...core.types.common import DonationError

from ....donation import models
from ..types import Donation
from ...core.types.base import BaseInputObjectType
from ...core.scalars import PositiveDecimal
from ...core.doc_category import DOC_CATEGORY_DONATIONS
from ...core.mutations import ModelMutation

from .utils import (
    validate_donation_price,
    validate_donation_quantity,
)

import graphene


class DonationCreateInput(BaseInputObjectType):
    id = graphene.ID(required=True, description="ID of the donation.")
    title = graphene.String(required=False, description="The title of the donation.")
    description = graphene.String(
        required=False, description="The description of the donation."
    )
    quantity = graphene.Int(required=False, description="The quantity of the donation.")
    price = PositiveDecimal(required=False, description="The price of the donation.")

    class Meta:
        doc_category = DOC_CATEGORY_DONATIONS


class DonationCreate(ModelMutation):
    success = graphene.Field(
        Donation, description="The donation created by this mutation."
    )

    class Arguments:
        input = DonationCreateInput(
            required=True,
            description="Fields required to create a donation.",
        )

    class Meta:
        description = "Create a new donation."
        doc_category = DOC_CATEGORY_DONATIONS
        model = models.Donation
        object_type = Donation
        return_field_name = "donation"
        error_type_class = DonationError
        error_type_fields = "donation_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.DONATION_CREATED,
                description="A donation has been created.",
            )
        ]

    @classmethod
    def validate_donation_input(cls, info: ResolveInfo, instance: models.Donation):
        validate_donation_price(instance)
        validate_donation_quantity(instance)

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance: models.Donation, data):
        cleaned_input = super().clean_input(info, instance, data)
        cls.validate_donation_input(info, instance)
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, input):
        input["user"] = info.context.user
        input["currency"] = "AXB"
        super().perform_mutation(_root, info, input=input)
        return DonationCreate(success=True, errors=[])
