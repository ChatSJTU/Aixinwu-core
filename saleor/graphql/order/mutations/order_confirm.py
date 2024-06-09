from typing import cast

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from saleor.graphql.core.enums import PaymentErrorCode
from saleor.graphql.core.types.common import PaymentError
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
        permissions = (OrderPermissions.MANAGE_ORDERS,)
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
        user = cast(User, user)
        order: models.Order = cls.get_instance(info, **data)
        cls.check_channel_permissions(info, [order.channel_id])
        order.status = OrderStatus.UNFULFILLED
        update_order_display_gross_prices(order)

        order.save(update_fields=["status", "updated_at", "display_gross_prices"])

        order_info = fetch_order_info(order)

        if user.balance >= order.total_net_amount:
            _ = create_payment(
                gateway="Balance",
                total=order.total_net_amount,
                currency="AXB",
                email=order_info.customer_email,
                customer_ip_address="",
                order=order,
            )

            order.status = OrderStatus.FULFILLED
            user.balance -= order.total_net_amount
            order.save(update_fields=["status"])
            user.save(update_fields=["balance"])
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
