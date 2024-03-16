from django.forms import ValidationError
from ...core.enums import DonationErrorCode
from ....donation import models


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
