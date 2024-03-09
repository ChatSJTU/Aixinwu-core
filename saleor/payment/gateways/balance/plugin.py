from typing import TYPE_CHECKING

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

from ..utils import get_supported_currencies
from . import (
    GatewayConfig,
    get_client_token,
    process_payment,
)

GATEWAY_NAME = "Account Balance"

if TYPE_CHECKING:
    from ...interface import GatewayResponse, PaymentData, TokenConfig


class BalanceGatewayPlugin(BasePlugin):
    PLUGIN_ID = "aixinwu.payments.balance"
    PLUGIN_NAME = GATEWAY_NAME
    DEFAULT_ACTIVE = False
    DEFAULT_CONFIGURATION = [
        {"name": "Store customers card", "value": False},
        {"name": "Automatic payment capture", "value": True},
        {"name": "Supported currencies", "value": "AXB"},
    ]
    CONFIG_STRUCTURE = {
        "Store customers card": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should store cards.",
            "label": "Store customers card",
        },
        "Automatic payment capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should automatically capture payments.",
            "label": "Automatic payment capture",
        },
        "Supported currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines currencies supported by gateway."
            " Please enter currency codes separated by a comma.",
            "label": "Supported currencies",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration["Automatic payment capture"],
            supported_currencies=configuration["Supported currencies"],
            connection_params={},
            store_customer=configuration["Store customers card"],
        )

    def _get_gateway_config(self):
        return self.config

    def authorize_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        raise NotImplementedError()

    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        raise NotImplementedError()

    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        raise NotImplementedError()

    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        raise NotImplementedError()

    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        raise NotImplementedError()

    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value
        return process_payment(payment_information, self._get_gateway_config())

    def get_client_token(self, token_config: "TokenConfig", previous_value):
        if not self.active:
            return previous_value
        return get_client_token()

    def get_supported_currencies(self, previous_value):
        if not self.active:
            return previous_value
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    def get_payment_config(self, previous_value):
        if not self.active:
            return previous_value
        config = self._get_gateway_config()
        return [{"field": "store_customer_card", "value": config.store_customer}]
