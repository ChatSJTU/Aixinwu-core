from typing import Optional, cast

import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....giftcard.utils import deactivate_order_gift_cards
from ....order import OrderStatus, models
from ....order.actions import cancel_order
from ....order.error_codes import OrderErrorCode
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order


def clean_order_cancel(order: Optional[models.Order]) -> models.Order:
    if not order or not order.can_cancel():
        raise ValidationError(
            {
                "order": ValidationError(
                    "This order can't be canceled.",
                    code=OrderErrorCode.CANNOT_CANCEL_ORDER.value,
                )
            }
        )
    return order


def check_order_ownership(order: Optional[models.Order], user):
    if not (user.is_superuser or user.is_staff):
        if order.user.id != user.id:
            raise ValidationError(
                {
                    "order": ValidationError(
                        "This order can not be manipulated by the current user.",
                        code=OrderErrorCode.CANNOT_CANCEL_ORDER.value,
                    )
                }
            )
        else:
            if order.status != OrderStatus.UNCONFIRMED:
                raise ValidationError(
                    {
                        "order": ValidationError(
                            "Normal users can only cancel orders that are not fulfilled.",
                            code=OrderErrorCode.CANNOT_CANCEL_ORDER.value,
                        )
                    }
                )
    return order


class OrderCancel(BaseMutation):
    order = graphene.Field(Order, description="Canceled order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to cancel.")

    class Meta:
        description = "Cancel an order."
        doc_category = DOC_CATEGORY_ORDERS
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        user = info.context.user
        order = cls.get_node_or_error(info, id, only_type=Order)
        # cls.check_channel_permissions(info, [order.channel_id])
        order = clean_order_cancel(order)
        order = check_order_ownership(order, user)

        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            cancel_order(
                order=order,
                user=user,
                app=app,
                manager=manager,
            )
            deactivate_order_gift_cards(order.id, user, app)
        return OrderCancel(order=order)
