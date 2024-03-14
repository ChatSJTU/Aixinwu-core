from django.forms import ValidationError
from ...core.enums import DonationErrorCode
from ....donation import models


def validate_donation_price(donation: models.Donation):
    if donation.price <= 0:
        raise ValidationError(
            {
                "price": ValidationError(
                    "Price must be greater than 0.",
                    code=DonationErrorCode.INVALID,
                )
            }
        )


def validate_donation_quantity(donation: models.Donation):
    if donation.quantity <= 0:
        raise ValidationError(
            {
                "quantity": ValidationError(
                    "Quantity must be greater than 0.",
                    code=DonationErrorCode.INVALID,
                )
            }
        )
