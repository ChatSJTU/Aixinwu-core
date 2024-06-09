from ast import Store
import uuid

from django.db import transaction

from saleor.graphql.payment.mutations import stored_payment_methods
from saleor.order import OrderStatus
from ... import ChargeStatus, StorePaymentMethod, TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData, PaymentMethodInfo
from ....account.models import User
from ....order.models import Order
from ....payment.models import Payment
from ....payment import ChargeStatus


def dummy_success():
    return True


def get_client_token(**_):
    return str(uuid.uuid4())


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    amount = payment_information.amount
    with transaction.atomic():
        user = User.objects.get(pk=payment_information.customer_id)
        if user.balance < amount:
            return GatewayResponse(
                is_success=False,
                action_required=False,
                kind=TransactionKind.VOID,
                amount=amount,
                currency=payment_information.currency,
                transaction_id=get_client_token(),
                error="Insufficient funds",
                raw_response={"error": "Insufficient funds"},
            )
        else:
            user.balance -= amount
            user.save()
            order = Order.objects.get(pk=payment_information.order_id)
            order.status = OrderStatus.FULFILLED
            order.save()
            payment = Payment.objects.create(
                gateway="AXB",
                currency="AXB",
                charge_status=ChargeStatus.FULLY_CHARGED,
                total=payment_information.amount,
                checkout=None,
                order=order,
                stored_payment_methods=StorePaymentMethod.OFF_SESSION,
            )
            return GatewayResponse(
                is_success=True,
                action_required=False,
                kind=TransactionKind.CAPTURE,
                amount=amount,
                currency=payment_information.currency,
                transaction_id=get_client_token(),
                error=None,
                raw_response={"status": "ok"},
            )
