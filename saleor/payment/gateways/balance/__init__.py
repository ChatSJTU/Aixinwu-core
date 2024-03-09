import uuid

from ... import ChargeStatus, TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData, PaymentMethodInfo
from ....account.models import User


def dummy_success():
    return True


def get_client_token(**_):
    return str(uuid.uuid4())


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    amount = payment_information.amount
    user = User.objects.get(pk=payment_information.customer_id)
    if user.balance < amount:
        return GatewayResponse(
            is_success=False,
            action_required=False,
            kind=TransactionKind.CONFIRM,
            amount=amount,
            currency=payment_information.currency,
            transaction_id=get_client_token(),
            error="Insufficient funds",
            raw_response={"error": "Insufficient funds"},
        )
    else:
        user.balance -= int(amount)
        user.save()
        return GatewayResponse(
            is_success=True,
            action_required=False,
            kind=TransactionKind.CONFIRM,
            amount=amount,
            currency=payment_information.currency,
            transaction_id=get_client_token(),
            error=None,
            raw_response={"status": "ok"},
        )
