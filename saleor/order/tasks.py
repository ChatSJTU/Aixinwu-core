import logging
from datetime import timedelta

from django.db.models import Exists, F, Func, OuterRef, Subquery, Value
from django.utils import timezone

from saleor.order.actions import create_fulfillments_for_expired_orders
from saleor.payment import ChargeStatus

from ..celeryconf import app
from ..channel.models import Channel
from ..core.tracing import traced_atomic_transaction
from ..core.utils.events import call_event
from ..discount.models import Voucher, VoucherCode, VoucherCustomer
from ..payment.gateway import _fetch_gateway_response
from ..payment.models import Payment, TransactionItem
from ..payment.utils import create_payment_information
from ..plugins.manager import get_plugins_manager
from ..warehouse.management import deallocate_stock_for_orders, remove_reservations_for_order
from . import OrderChargeStatus, OrderEvents, OrderStatus
from .models import Order, OrderEvent
from .utils import invalidate_order_prices

logger = logging.getLogger(__name__)

# Batch size of 100 is about ~1MB of memory usage in task
EXPIRE_ORDER_BATCH_SIZE = 100

# Batch size of 5000 is about ~5MB of memory usage in task
# It takes +/- 8 secs to delete 5000 orders
DELETE_EXPIRED_ORDER_BATCH_SIZE = 5000


@app.task
def recalculate_orders_task(order_ids: list[int]):
    orders = Order.objects.filter(id__in=order_ids)

    for order in orders:
        invalidate_order_prices(order)

    Order.objects.bulk_update(orders, ["should_refresh_prices"])


@app.task
def send_order_updated(order_ids):
    manager = get_plugins_manager(allow_replica=True)
    for order in Order.objects.filter(id__in=order_ids):
        manager.order_updated(order)


def _bulk_release_voucher_usage(order_ids):
    voucher_orders = Order.objects.filter(
        voucher_code=OuterRef("code"),
        id__in=order_ids,
    )
    count_orders = voucher_orders.annotate(
        count=Func(F("pk"), function="Count")
    ).values("count")

    vouchers = Voucher.objects.filter(usage_limit__isnull=False)
    VoucherCode.objects.filter(
        Exists(voucher_orders),
        Exists(vouchers.filter(id=OuterRef("voucher_id"))),
    ).annotate(order_count=Subquery(count_orders)).update(
        used=F("used") - F("order_count")
    )

    orders = Order.objects.filter(id__in=order_ids)
    voucher_codes = VoucherCode.objects.filter(
        Exists(orders.filter(voucher_code=OuterRef("code")))
    )
    VoucherCustomer.objects.filter(
        Exists(voucher_codes.filter(id=OuterRef("voucher_code_id"))),
        Exists(orders.filter(user_email=OuterRef("customer_email"))),
    ).delete()


def _call_expired_order_events(order_ids, manager):
    orders = Order.objects.filter(id__in=order_ids)
    for order in orders:
        call_event(manager.order_expired, order)
        call_event(manager.order_updated, order)


def _order_expired_events(order_ids):
    OrderEvent.objects.bulk_create(
        [
            OrderEvent(
                order_id=order_id,
                type=OrderEvents.EXPIRED,
            )
            for order_id in order_ids
        ]
    )


def _expire_orders(manager, now):
    time_diff_func_in_minutes = (
        Func(Value("day"), now - OuterRef("created_at"), function="DATE_PART") * 24
        + Func(Value("hour"), now - OuterRef("created_at"), function="DATE_PART") * 60
    ) + Func(Value("minute"), now - OuterRef("created_at"), function="DATE_PART")

    channels = Channel.objects.filter(
        id=OuterRef("channel"),
        expire_orders_after__isnull=False,
        expire_orders_after__gt=0,
        expire_orders_after__lte=time_diff_func_in_minutes,
    )

    # 未支付订单
    qs = Order.objects.filter(
        Exists(channels),
        charge_status__in=[ChargeStatus.NOT_CHARGED, OrderChargeStatus.NONE],
        status__in=[OrderStatus.UNCONFIRMED],
    )
    ids_batch = list(qs.values_list("pk", flat=True)[:EXPIRE_ORDER_BATCH_SIZE])
    logger.warning(f"expired order (unpaid): {len(ids_batch)}")
    with traced_atomic_transaction():
        _bulk_release_voucher_usage(ids_batch)
        _order_expired_events(ids_batch)
        deallocate_stock_for_orders(ids_batch, manager)
        _call_expired_order_events(ids_batch, manager)
        Order.objects.filter(id__in=ids_batch).update(
            status=OrderStatus.EXPIRED, expired_at=now
        )

    # 已支付未交付订单
    qs = Order.objects.filter(
        Exists(channels),
        status__in=[OrderStatus.UNCONFIRMED, OrderStatus.UNFULFILLED, OrderStatus.PARTIALLY_FULFILLED],
    )
    orders = list(qs.all())
    logger.warning(f"expired order count: {len(orders)}")
    for order in orders:
        try:
            with traced_atomic_transaction():
                remove_reservations_for_order(order=order)
                create_fulfillments_for_expired_orders(order, manager)
                order.status = OrderStatus.EXPIRED
                order.expired_at = timezone.now()
                order.save(update_fields=["status", "updated_at"])
                OrderEvent.objects.create(
                    order=order,
                    type=OrderEvents.EXPIRED,
                )
        except Exception as e:
            logger.error(e)
        # Order.objects.filter(id__in=ids_batch).update(
        #     status=OrderStatus.EXPIRED, expired_at=now
        # )
        # _bulk_release_voucher_usage(ids_batch)
        # _order_expired_events(ids_batch)
        # deallocate_stock_for_orders(ids_batch, manager)
        # _call_expired_order_events(ids_batch, manager)


@app.task
def expire_orders_task():
    logger.warning(f"===expire_orders_task===")
    now = timezone.now()
    manager = get_plugins_manager(allow_replica=False)
    _expire_orders(manager, now)


# @app.task
# def delete_expired_orders_task():
#     now = timezone.now()

#     channel_qs = Channel.objects.filter(
#         delete_expired_orders_after__gt=timedelta(),
#         id=OuterRef("channel"),
#     )

#     qs = Order.objects.annotate(
#         delete_expired_orders_after=Subquery(
#             channel_qs.values("delete_expired_orders_after")[:1]
#         )
#     ).filter(
#         ~Exists(TransactionItem.objects.filter(order=OuterRef("pk"))),
#         ~Exists(Payment.objects.filter(order=OuterRef("pk"))),
#         expired_at__isnull=False,
#         status=OrderStatus.EXPIRED,
#         expired_at__lte=now - F("delete_expired_orders_after"),  # type:ignore
#     )
#     ids_batch = qs.values_list("pk", flat=True)[:DELETE_EXPIRED_ORDER_BATCH_SIZE]
#     if not ids_batch:
#         return
#     Order.objects.filter(id__in=ids_batch).delete()
#     delete_expired_orders_task.delay()
