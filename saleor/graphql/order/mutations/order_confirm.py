from typing import cast

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from saleor.core.prices import quantize_price
from saleor.core.tracing import traced_atomic_transaction
from saleor.graphql.core.enums import PaymentErrorCode
from saleor.graphql.core.types.common import PaymentError
from saleor.order import events as order_events
from saleor.account import events as account_events
from saleor.payment import ChargeStatus
from saleor.payment.utils import create_payment

from ....account.models import User
from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ....order.fetch import fetch_order_info
from ....order.utils import update_order_display_gross_prices
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import OrderError
from ...site.dataloaders import get_site_promise
from ..types import Order


class OrderConfirm(ModelMutation):
    order = graphene.Field(Order, description="Order which has been confirmed.")

    class Arguments:
        id = graphene.ID(description="ID of an order to confirm.", required=True)

    class Meta:
        description = "Confirms an unconfirmed order by changing status to unfulfilled."
        model = models.Order
        object_type = Order
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        instance = super().get_instance(info, **data)
        if not instance.is_unconfirmed():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to an order with status "
                        "different than unconfirmed.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )
        if not instance.lines.exists():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to an order without products.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )
        return instance

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        user = info.context.user
        if not user:
            raise ValidationError(
                {
                    "user": ValidationError(
                        "User not found.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )
        user = cast(User, user)
        order: models.Order = cls.get_instance(info, user=user, **data)
        if not order:
            raise ValidationError(
                {
                    "order": ValidationError(
                        "No order found for this id.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )

        update_order_display_gross_prices(order)

        order.save(update_fields=["status", "updated_at", "display_gross_prices"])

        order_info = fetch_order_info(order)

        if user.balance >= order.total_net_amount:
            with traced_atomic_transaction():
                payment = order.get_last_payment()
                order.status = OrderStatus.UNFULFILLED
                order.charge_status = ChargeStatus.FULLY_CHARGED
                order.total_charged_amount = order.total_net_amount
                payment.charge_status = ChargeStatus.FULLY_CHARGED
                payment.captured_amount = order.total_net_amount
                user.balance -= order.total_net_amount
                user.balance = quantize_price(user.balance, "AXB")
                order.save(
                    update_fields=["status", "charge_status", "total_charged_amount"]
                )
                user.save(update_fields=["balance"])
                payment.save(update_fields=["charge_status", "captured_amount"])
                order_events.order_confirmed_event(order=order, user=user, app=None)
                account_events.consumption_balance_event(user=user, order=order)
                return OrderConfirm(order=order)
        else:
            raise ValidationError(
                {
                    "balance": ValidationError(
                        "You need to have enough balance",
                        code=PaymentErrorCode.BALANCE_CHECK_ERROR,
                    )
                }
            )
