import graphene

from saleor.graphql.app.enums import description

from ...account import models as account_models
from ...order import models as order_models
from ..account.types import CustomerEvent
from ..core import ResolveInfo
from ..core.connection import CountableConnection
from ..core.doc_category import DOC_CATEGORY_EVENTS
from ..core.types.model import ModelObjectType


class BalanceEvent(ModelObjectType[account_models.BalanceEvent]):
    id = graphene.ID(required=True, description="The ID of the balance event.")
    number = graphene.String(description="The number of the balance event.")
    account = graphene.String(description="User account of a balance event.")
    balance = graphene.Float(description="Balance of a balance event.")
    delta = graphene.Float(description="Delta of a balance event.")
    type = graphene.String(description="Type of a balance event.")
    name = graphene.String(description="User name of a balance event.")
    code = graphene.String(description="Code of the customer.")
    date = graphene.DateTime(description="Datetime of the event.")

    class Meta:
        description = "Represents balance events."
        interfaces = [graphene.relay.Node]
        model = account_models.BalanceEvent

    @staticmethod
    def resolve_id(root, info: ResolveInfo):
        return graphene.Node.to_global_id("BalanceEvent", root.pk)

    @staticmethod
    def resolve_balance(root, info: ResolveInfo):
        return root.balance

    @staticmethod
    def resolve_delta(root, info: ResolveInfo):
        return root.delta

    @staticmethod
    def resolve_number(root, info: ResolveInfo):
        if not root.date or not root.number:
            return None
        return root.date.strftime("%y%m") + str(root.number).zfill(4)

    @staticmethod
    def resolve_date(root, info: ResolveInfo):
        return root.date

    @staticmethod
    def resolve_type(root, info: ResolveInfo):
        return root.type

    @staticmethod
    def resolve_account(root, info: ResolveInfo):
        return root.user.account

    @staticmethod
    def resolve_name(root, info: ResolveInfo):
        return root.user.first_name

    @staticmethod
    def resolve_code(root, info: ResolveInfo):
        return root.user.code


class OrderEvent(ModelObjectType[order_models.OrderEvent]):
    id = graphene.ID(required=True, description="The ID of the balance event.")
    date = graphene.DateTime(description="Datetime of the event.")

    class Meta:
        description = "Represents balance events."
        interfaces = [graphene.relay.Node]
        model = order_models.OrderEvent

    @staticmethod
    def resolve_id(root, info: ResolveInfo):
        return root.id

    @staticmethod
    def resolve_date(root, info: ResolveInfo):
        return root.date


class BalanceEventCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_EVENTS
        node = BalanceEvent


class CustomerEventCountableConnection(CountableConnection):
    class Meta:
        doc_category = DOC_CATEGORY_EVENTS
        node = CustomerEvent
