from django.forms import ValidationError

from saleor.graphql.core import ResolveInfo
from saleor.graphql.utils import get_user_or_app_from_context
from saleor.permission.enums import DonationPermissions
from saleor.permission.utils import has_one_of_permissions
from ...core.enums import DonationErrorCode
from ....donation import DonationStatus, models


def validate_donation_price(input):
    if input["price"].amount <= 0:
        raise ValidationError(
            {
                "price": ValidationError(
                    "Price must be greater than 0.",
                    code=DonationErrorCode.INVALID,
                )
            }
        )


def validate_donation_quantity(input):
    if input["quantity"] <= 0:
        raise ValidationError(
            {
                "quantity": ValidationError(
                    "Quantity must be greater than 0.",
                    code=DonationErrorCode.INVALID,
                )
            }
        )


def validate_create_permission(info: ResolveInfo, instance: models.Donation):
    requestor = get_user_or_app_from_context(info.context)

    if not requestor or not has_one_of_permissions(
        requestor,
        [DonationPermissions.MANAGE_DONATIONS, DonationPermissions.ADD_DONATIONS],
    ):
        raise ValidationError(
            {
                "requestor": ValidationError(
                    "Requestor did not have the permission",
                    code=DonationErrorCode.PERMISSION_DENIED,
                )
            }
        )


def validate_update_permission(info: ResolveInfo, instance: models.Donation):
    requestor = get_user_or_app_from_context(info.context)

    if not requestor:
        raise ValidationError(
            {
                "requestor": ValidationError(
                    "Requestor did not have the permission",
                    code=DonationErrorCode.PERMISSION_DENIED,
                )
            }
        )
    if instance.status == DonationStatus.COMPLETED and not has_one_of_permissions(
        requestor,
        [DonationPermissions.MANAGE_DONATIONS],
    ):
        raise ValidationError(
            {
                "donation": ValidationError(
                    "This donation is completed thus constant.",
                    code=DonationErrorCode.INVALID,
                )
            }
        )
    if instance.status != DonationStatus.COMPLETED and not has_one_of_permissions(
        requestor,
        [DonationPermissions.ADD_DONATIONS],
    ):
        raise ValidationError(
            {
                "requestor": ValidationError(
                    "Requestor did not have the permission",
                    code=DonationErrorCode.PERMISSION_DENIED,
                )
            }
        )


def validate_complete_permission(info: ResolveInfo, instance: models.Donation):
    requestor = get_user_or_app_from_context(info.context)

    if not requestor or not has_one_of_permissions(
        requestor,
        [DonationPermissions.MANAGE_DONATIONS],
    ):
        raise ValidationError(
            {
                "requestor": ValidationError(
                    "Requestor did not have the permission",
                    code=DonationErrorCode.PERMISSION_DENIED,
                )
            }
        )
