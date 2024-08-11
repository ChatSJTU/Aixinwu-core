from django.forms import ValidationError

from saleor.account.models import User

from ....donation import DonationStatus, models
from ....permission.enums import DonationPermissions
from ....permission.utils import has_one_of_permissions
from ...core import ResolveInfo
from ...core.context import get_database_connection_name
from ...core.enums import DonationErrorCode
from ...utils import get_user_or_app_from_context


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


def validate_donation_barcode(info: ResolveInfo, instance, input):
    if (
        models.Donation.objects.using(get_database_connection_name(info.context))
        .exclude(pk=instance.pk)
        .filter(barcode=input["barcode"])
        .exists()
    ):
        raise ValidationError(
            {
                "barcode": ValidationError(
                    "Barcode should not be duplicated for donation",
                    code=DonationErrorCode.INVALID,
                )
            }
        )


def validate_donator(info: ResolveInfo, input):
    if (
        not User.objects.using(get_database_connection_name(info.context))
        .filter(code=input.get("donator", "invalid"))
        .exists()
    ):
        raise ValidationError(
            {
                "donator": ValidationError(
                    "Donator does not exist", code=DonationErrorCode.INVALID
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
